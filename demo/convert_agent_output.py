import json
import os
import uuid
from evaluate_module.schemas import AgentOutputItem, ToolUse

def convert_agent_outputs():
    """
    将results目录下所有json文件（如results_test_20250621_101809.json）转换为schemas.py中的AgentOutputItem格式，并保存为json。
    """
    results_dir = "results"
    output_dir = "converted_agent_outputs"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    json_files = [f for f in os.listdir(results_dir) if f.endswith(".json")]

    total_count = 0

    for json_file in json_files:
        file_path = os.path.join(results_dir, json_file)
        with open(file_path, "r", encoding="utf-8") as f:
            try:
                results = json.load(f)
            except Exception as e:
                print(f"文件{json_file}解析失败: {e}")
                continue

        # 针对results_test_20250621_101809.json的结构进行处理
        # 该文件为一个list，每个元素为一个turn，包含task_id, question, answer, tool_calls等
        converted_outputs = []

        # 判断是list还是dict
        if isinstance(results, dict):
            # 兼容单个dict的情况
            results = [results]

        for item in results:
            try:
                # 检查item是否包含必要的字段
                if not isinstance(item, dict):
                    print(f"跳过非字典项: {item}")
                    continue
                    
                # 获取answer，支持多种数据结构
                answer = None
                if 'result' in item and isinstance(item['result'], list) and len(item['result']) > 0:
                    answer = item['result'][0]
                elif 'result' in item and isinstance(item['result'], str):
                    answer = item['result']
                elif 'answer' in item:
                    answer = item['answer']
                else:
                    print(f"跳过缺少answer/result字段的项: task_id={item.get('task_id', 'unknown')}")
                    continue
                    
                task_id = item.get("task_id", None)
                question = item.get("question", None)
                
                # 如果没有task_id或question，也跳过
                if not task_id or not question:
                    print(f"跳过缺少task_id或question的项: task_id={task_id}, question={question}")
                    continue

                # 处理tool_calls
                tool_use_list = []
                tool_calls = item.get("tool_calls", [])
                for tool_call in tool_calls:
                    tool_use = ToolUse(
                        call_id=str(uuid.uuid4()),
                        tool_name=tool_call.get("tool_name", ""),
                        tool_description=tool_call.get("tool_description", ""),
                        tool_input=json.dumps(tool_call.get("arguments", {}), ensure_ascii=False),
                        tool_output=tool_call.get("tool_output", None)
                    )
                    tool_use_list.append(tool_use)

                # 构造AgentOutputItem
                output_item = AgentOutputItem(
                    task_id=task_id,
                    question=question,
                    answer=answer,
                    # schemas.py中AgentOutputItem只需要answer, task_id, question
                    # 其余字段如tool_use_list, reasoning_list不是必需
                )
                converted_outputs.append(output_item)
                
            except Exception as e:
                print(f"处理单个项时出错: {e}, item: {item}")
                continue

        # 保存
        output_file = os.path.join(output_dir, f"converted_{json_file}")
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump([item.dict() for item in converted_outputs], f, indent=2, ensure_ascii=False)

        print(f"已转换 {len(converted_outputs)} 条记录，保存至 {output_file}")
        total_count += len(converted_outputs)

    print(f"所有文件共转换 {total_count} 条记录，已保存至 {output_dir}。")

if __name__ == "__main__":
    convert_agent_outputs()
