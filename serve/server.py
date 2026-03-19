from fastapi import FastAPI, Request
from fastapi.responses import Response, HTMLResponse
import uuid
import time

app = FastAPI()

# 内存里的“待下发命令”（最简，重启会丢；答辩足够用）
pending = None

@app.get("/")
def index():
    # 直接把 control.html 的内容返回（你也可以单独放静态文件）
    html = open("control.html", "r", encoding="utf-8").read()
    return HTMLResponse(html)

@app.post("/api/command")
async def create_command(req: dict):
    """
    控制端下发命令：
    {
      "buzzer_override": 1,
      "buzzer_mode": 1,
      "led1": 1,
      "led2": 0
    }
    """
    global pending
    pending = {
        "command_id": str(uuid.uuid4()),
        "created_at": time.time(),
        "buzzer_override": int(req.get("buzzer_override", 0)),
        "buzzer_mode": int(req.get("buzzer_mode", 0)),  # 0=OFF,1=CONTINUOUS,2=INTERMITTENT
        "led1": int(req.get("led1", 0)),
        "led2": int(req.get("led2", 0)),
    }
    return {"ok": True, "pending": pending}

@app.post("/api/ack")
async def ack(req: dict):
    """
    设备执行后回执（可选，但建议做，避免重复执行）
    {
      "command_id": "...",
      "result": "ok"
    }
    """
    global pending
    if pending and req.get("command_id") == pending["command_id"] and req.get("result") == "ok":
        pending = None
    return {"ok": True}

@app.post("/api/data")
async def upload_data(request: Request):
    """
    设备上报接口：STM32 POST 到这里。
    服务器用“响应头”把命令带回去（STM32解析最简单）。
    """
    global pending
    _ = await request.json()  # 你要存数据可在这里写入文件/数据库；最简先不存

    headers = {}
    if pending:
        headers["X-COMMAND-ID"] = pending["command_id"]
        headers["X-BUZZER-OVERRIDE"] = str(pending["buzzer_override"])
        headers["X-BUZZER-MODE"] = str(pending["buzzer_mode"])
        headers["X-LED1"] = str(pending["led1"])
        headers["X-LED2"] = str(pending["led2"])
    else:
        headers["X-BUZZER-OVERRIDE"] = "0"

    return Response(content=b"", status_code=200, headers=headers)