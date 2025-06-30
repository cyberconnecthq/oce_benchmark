import os
import json
import uuid
import shutil

def replace_task_ids():
    oce_eval_path = "dataset/oce_eval_data.json"
    tasks_dir = "dataset/tasks"

    # 读取oce_eval_data.json
    with open(oce_eval_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 构建旧id到新id的映射
    id_map = {}
    for item in data:
        old_id = item["task_id"]
        new_id = str(uuid.uuid4())
        id_map[old_id] = new_id
        item["task_id"] = new_id

    # 保存新的oce_eval_data.json
    with open(oce_eval_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    # 遍历tasks目录，重命名文件
    for old_id, new_id in id_map.items():
        old_file = os.path.join(tasks_dir, f"{old_id}")
        new_file = os.path.join(tasks_dir, f"{new_id}")
        if os.path.exists(old_file):
            shutil.move(old_file, new_file)
        else:
            print(f"警告: 未找到文件 {old_file}")

if __name__ == "__main__":
    replace_task_ids()
