# Syncing Backend to HuggingFace Space

The HF Space repo lives at `~/Documents/github_work/hf_spaces/A2XTbB49wS`. Whenever backend source changes, sync it:

```bash
# From project root
rsync -av --delete \
  --exclude='__pycache__' \
  backend/Dockerfile \
  backend/.dockerignore \
  backend/.env.example \
  backend/pyproject.toml \
  backend/uv.lock \
  ~/Documents/github_work/hf_spaces/A2XTbB49wS/

rsync -av --delete \
  --exclude='__pycache__' \
  backend/rta_backend/ \
  ~/Documents/github_work/hf_spaces/A2XTbB49wS/rta_backend/

# Commit and push
cd ~/Documents/github_work/hf_spaces/A2XTbB49wS
git add . && git commit -m "sync: backend update" && git push origin main
```

**Always sync after modifying any file in `backend/rta_backend/` or the Dockerfile.**
