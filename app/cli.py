# cli.py - 命令行工具
import click
import json
import asyncio
from pathlib import Path
from oce_evaluator import OCEEvaluator, quick_evaluate
from schemas import AgentOutputItem

@click.group()
def cli():
    """OCE Benchmark CLI工具"""
    pass

@cli.command()
@click.option('--task-id', required=True, help='任务ID')
@click.option('--answer', required=True, help='代理答案')
@click.option('--model', default='gpt-4.1', help='模型名称')
@click.option('--output', '-o', help='输出文件路径')
def evaluate(task_id, answer, model, output):
    """评估单个任务"""
    result = asyncio.run(quick_evaluate(task_id, answer, model))
    
    if output:
        with open(output, 'w') as f:
            json.dump(result, f, indent=2)
        click.echo(f"结果已保存到: {output}")
    else:
        click.echo(json.dumps(result, indent=2))

@cli.command()
@click.option('--input-file', '-i', required=True, help='输入JSON文件')
@click.option('--output-file', '-o', help='输出结果文件')
@click.option('--model', default='gpt-4.1', help='模型名称')
def batch(input_file, output_file, model):
    """批量评估"""
    with open(input_file) as f:
        data = json.load(f)
    
    agent_outputs = [AgentOutputItem(**item) for item in data]
    
    evaluator = OCEEvaluator()
    results = asyncio.run(evaluator.evaluate_batch(agent_outputs, model))
    
    output_path = output_file or f"results_{Path(input_file).stem}.json"
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    click.echo(f"批量评估完成，结果保存到: {output_path}")

@cli.command()
def health():
    """健康检查"""
    try:
        evaluator = OCEEvaluator()
        # 简单的连接测试
        latest_block = evaluator.w3.eth.get_block('latest')
        click.echo(f"✅ 连接正常，当前区块: {latest_block.number}")
    except Exception as e:
        click.echo(f"❌ 连接失败: {e}")
        exit(1)

if __name__ == '__main__':
    cli()