# Python 的静态类型检查，只在 IDE 中生效，运行时不强制校验
# TypedDict 定义一个字典类型，用来给字典规定固定的键和类型
# Literal 定义一个类型，只能取指定的值，限定变量只能取几个指定值
from typing import TypedDict,Literal
from fastapi import FastAPI
from langgraph import StateGraph,START,END
# 检查点中断 状态用 MemorySaver 保存到内存
from langgraph.checkpointer.memory import MemorySaver
from pydantic import BaseModel
from langgraph.types import Command

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
    checkpointer=checkpointer,
    interrupt_before=["human_review"],
)
