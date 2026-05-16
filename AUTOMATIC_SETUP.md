# 🤖 Automatic Setup Guide

`setup.sh` now supports **fully automatic deployment** via environment variables!

## Quick Start

### Interactive (User-Friendly)
```bash
sudo bash setup.sh
# Follow the prompts
```

### Automatic (100% No User Input)
```bash
export TG_TOKEN="your_token"
export TG_CHAT_ID="-1001234567890"
export ADMIN_IDS="123456789"
export RCON_PASSWORD="your_password"
export AUTO_RCLONE="skip"

sudo -E bash setup.sh
```

## Full Guide

See [docs/AUTOMATIC_SETUP.md](docs/AUTOMATIC_SETUP.md) for:
- Detailed environment variable reference
- One-liner automatic deploy
- Docker & Kubernetes examples
- CI/CD pipeline setup
- Troubleshooting

---

**Supports both modes! Choose what works for you. 🚀**
