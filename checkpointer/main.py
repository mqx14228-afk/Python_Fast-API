# 搭建一条工作流，跑到 human_review 之前自动暂停、保存状态；
# 外部通过接口发起审核，审核通过后恢复继续跑，拒绝就停住；
# 用 thread_id 隔离不同会话状态。

# Python 的静态类型检查，只在 IDE 中生效，运行时不强制校验
# TypedDict 定义一个字典类型，用来给字典规定固定的键和类型
# Literal 定义一个类型，只能取指定的值，限定变量只能取几个指定值
from typing import TypedDict,Literal
from fastapi import FastAPI
from langgraph.graph import StateGraph,START,END
# 检查点中断 状态用 MemorySaver 保存到内存
from langgraph.checkpoint.memory import MemorySaver
from pydantic import BaseModel
from langgraph.types import Command
from typing import Any

# Annotation.Root 
# TypeDict 基类 作用是给字典规定固定的键和类型
class WorkflowState(TypedDict):
    step:int
    msg:str

# 工作节点1
def node1(state:WorkflowState) -> dict:
    print("执行节点1")
    return {"step":1,"msg":"节点1 执行完成"}

# 工作节点2
def node2(state:WorkflowState) -> dict:
    print("执行节点2")
    return {"step":2,"msg":"节点2 执行完成，等待人工审核"}

# 人工审核节点
def human_review(state:WorkflowState) -> dict:
    print("人工审核通过，进入节点3")
    return {"step":3,"msg":"人工审核节点执行完成"}

def node4(state:WorkflowState) -> dict:
    print("执行节点4，流程结束")
    return {"step":4,"msg":"节点4 执行完成"}

# StateGraph：LangGraph 的图构建器
# 新建一张状态图，规定这张图里流转的数据必须遵循 WorkflowState 的结构
builder = StateGraph(WorkflowState)
builder.add_node("node1",node1)
builder.add_node("node2",node2)
builder.add_node("human_review",human_review)
builder.add_node("node4",node4)

builder.add_edge(START,"node1")
builder.add_edge("node1","node2")
builder.add_edge("node2","human_review")
builder.add_edge("human_review","node4")
builder.add_edge("node4",END)

# 内存检查点存储器
# 先保存当前状态 再停下来
# 从保存状态恢复 继续执行
checkpointer = MemorySaver()

graph = builder.compile(
    # 检查点 标记中断并保存当前状态 便于恢复
    checkpointer=checkpointer,
    # 在人工审核节点之前中断 interrupt 中断执行
    interrupt_before=["human_review"],
)

app = FastAPI(title="LangGraph Human-in-the-Loop Demo")

# 用户输入 检验
class ResumeRequest(BaseModel):
    approved:bool

# configurable thread_id 是会话唯一标识，配合 checkpointer 存取图状态，实现会话状态的保存和恢复、对话隔离
def make_config(thread_id:str) -> dict:
    return {
        "configurable":{
            # 会话唯一标识 不同的用户 会话状态 会不同
            "thread_id":thread_id
        }
}

# 启动工作流并暂停在审核前
@app.post("/start")
def start_workflow(thread_id:str = "demo-thread-001"):
    config = make_config(thread_id)
    # result 是 LangGraph 图执行结束后返回的最终字典状态，包含节点输出与更新后的状态
    # invoke 之后 result 会包含暂停节点的信息
    result = graph.invoke({"step":0,"msg":""},config)
    print(result)
    # snapshot 是随时可查的、带中断、下一个节点等控制信息的完整状态视图
    snapshot = graph.get_state(config)
    print(snapshot)
    return {
        "status":"interrupted",
        "thread_id":thread_id,
        "current_state":result,
        "next_node":list[Any](snapshot.next),
        "message":"流程已暂停，等待人工审核"
    }

@app.post("/resume")
def resume_workflow(req:ResumeRequest,thread_id:str = "demo-thread-001"):
    config = make_config(thread_id)
    if not req.approved:
        return {
            "status":"rejected",
            "thread_id":thread_id,
            "message":"人工审核未通过，流程已经暂停"
        }

    # resume=True 从暂停节点继续执行 从 checkpointer 恢复状态继续执行
    final_state = graph.invoke(Command(resume=True),config)
    snapshot = graph.get_state(config)
    return {
        "status":"completed" if snapshot.next == 0 else "interrupted",
        "thread_id":thread_id,
        "final_state":final_state,
        "next_node":list[Any](snapshot.next),
        "message":"审核通过，流程继续执行"
    }

@app.get("/state")
def get_state(thread_id:str = "demo-thread-001"):
    config = make_config(thread_id)
    snapshot = graph.get_state(config)
    return {
        "thread_id":thread_id,
        "current_state":snapshot.values,
        "config":snapshot.config,
        "next_node":list[Any](snapshot.next),
    }
