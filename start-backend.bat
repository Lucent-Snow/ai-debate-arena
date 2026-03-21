@echo off
cd /d E:\Desktop\Program\ai-debate-arena
set AI_DEBATE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
set AI_DEBATE_API_KEY=sk-36a81727e2a541ee987395e4ed565135
set AI_DEBATE_MODEL=qwen-plus
python -m uvicorn run_server:app --host 0.0.0.0 --port 8080
pause
