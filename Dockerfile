# 3D 看板任务接入服务 —— 只依赖 Python 标准库，无需 pip install
# 镜像约 60MB，构建不需要联网装包
FROM python:3.12-slim

LABEL org.opencontainers.image.title="office-taskboard" \
      org.opencontainers.image.description="3D 办公室任务看板 + 与 agent 无关的任务接入 API"

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    BOARD_CONFIG=/app/board.config.json \
    BOARD_DATA_DIR=/app/data \
    BOARD_HOST=0.0.0.0 \
    BOARD_PORT=8787

WORKDIR /app

# 引擎（自带，保证镜像独立可用；运行时会被宿主机挂载的同名目录覆盖）
COPY taskboard/ /app/taskboard/
COPY board.config.json /app/board.config.json

# 运行时由 compose 把宿主机的内容挂进来：data / tasks-data / 看板 HTML / 模型包
RUN mkdir -p /app/data/inbox /app/tasks-data

EXPOSE 8787

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request,os,sys; \
u='http://127.0.0.1:'+os.environ.get('BOARD_PORT','8787')+'/api/health'; \
sys.exit(0 if urllib.request.urlopen(u,timeout=4).status==200 else 1)"

# 起服务 = 看板静态托管 + REST API + 投递箱自动扫描
CMD ["python", "-m", "taskboard", "serve"]
