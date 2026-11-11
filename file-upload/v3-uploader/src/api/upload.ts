import axios from "axios";

// axios 全局配置实例
const client = axios.create({
    baseURL: "/api",
    timeout: 10000,
});

// api 接口方法
// File 浏览器内置类型，用于表示文件对象
export function uploadFile(file: File) {
    // 表单提交 body 请求体
    const form = new FormData();
    form.append("file", file);

    // 泛型 泛指 promise resolve 值的类型 指定返回值类型
    // 泛型 T 类型作为参数
    return client.post<{
        // 0 成功 1 失败，错误
        code: number;
        // 错误信息
        message: string;
        // 上传成功后的数据 失败时 data 为空对象
        data: {
        original_name: string; // 原始文件名
        saved_name: string; // 保存后的文件名
        size: number; // 文件大小
        };
    }>("/upload", form, {
        headers: {
            // 附件、文件上传时，请求头的 Content-Type 必须设置为 multipart/form-data
            "Content-Type": "multipart/form-data",
        },
    });
}
