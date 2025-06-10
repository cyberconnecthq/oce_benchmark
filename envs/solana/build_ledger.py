"""
生成 ledger_v1_195.tar.zst，可复制上传
"""
import subprocess, yaml, shutil, os, tarfile, zstandard as zstd, time, requests, json
cfg = yaml.safe_load(open("envs/solana/manifest.yaml"))
ledger = "/tmp/ledger_build"

def check_validator_health(max_retries=30, delay=2):
    """检查validator是否已经启动并且健康"""
    for i in range(max_retries):
        try:
            response = requests.post(
                "http://127.0.0.1:8899",
                json={"jsonrpc": "2.0", "id": 1, "method": "getHealth"},
                timeout=5
            )
            if response.status_code == 200:
                result = response.json()
                if "result" in result:
                    print(f"Validator is healthy after {i * delay} seconds")
                    return True
        except Exception as e:
            print(f"Health check attempt {i+1}: {e}")
        time.sleep(delay)
    return False

# 清理可能存在的旧validator进程
subprocess.run(["pkill", "-f", "solana-test-validator"], capture_output=True)
time.sleep(2)

# 清理旧的ledger目录
if os.path.exists(ledger):
    shutil.rmtree(ledger)

print("启动 solana-test-validator...")
# 1) 启动一条干净 test‑validator 并 clone 所需账户
proc = subprocess.Popen([
    "solana-test-validator", "--ledger", ledger,
    "--url", "https://api.mainnet-beta.solana.com",
    *sum([["--clone", a] for a in cfg["clone"]], []),
    "--limit-ledger-size", "50000000",
    "--reset",
    "--quiet"  # 减少输出噪音
], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

print("等待validator启动和预热...")
if not check_validator_health():
    print("Validator启动失败，终止进程...")
    proc.terminate()
    proc.wait()
    # 输出错误信息进行调试
    stdout, stderr = proc.communicate()
    print("STDOUT:", stdout.decode())
    print("STDERR:", stderr.decode())
    raise Exception("Validator failed to start properly")

print("Validator启动成功，等待稳定...")
time.sleep(5)  # 额外等待时间确保稳定

print("终止validator...")
proc.terminate()
proc.wait()

print("开始打包 ledger...")
# 2) 打包 ledger
with tarfile.open(cfg["ledger_tar"].replace(".zst", ""), "w") as tar:
    tar.add(ledger, arcname="ledger")

print("开始Zstd压缩...")
# 3) Zstd 压缩
with open(cfg["ledger_tar"].replace(".zst", ""), "rb") as f_in, open(cfg["ledger_tar"], "wb") as f_out:
    c = zstd.ZstdCompressor(level=19)
    f_out.write(c.compress(f_in.read()))

# 清理临时文件
os.remove(cfg["ledger_tar"].replace(".zst", ""))
print(f"完成！生成文件：{cfg['ledger_tar']}")