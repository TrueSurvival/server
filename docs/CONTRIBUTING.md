# 🤝 Contributing Guide

Thanks for being interested in contributing! Here's how you can help.

---

## 📋 Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Help others learn
- Respect others' time and effort

---

## 🐛 Found a Bug?

### Report it here:
1. Check [existing issues](../../issues) first (don't duplicate)
2. Click "New Issue"
3. Choose "🐛 Bug Report"
4. Fill in the template with:
   - **Description:** What happened?
   - **Steps to Reproduce:** How to trigger it?
   - **Expected Behavior:** What should happen?
   - **Actual Behavior:** What actually happened?
   - **Environment:** OS, Java version, server version
   - **Logs:** Any error messages?

### Example:
```
Title: Bot crashes when /backup runs during server startup

Description:
When executing /backup command within 30 seconds of server startup, 
the bot crashes with "RCON connection timeout".

Steps to Reproduce:
1. Restart minecraft.service
2. Immediately run /backup in Telegram
3. Bot crashes

Expected: Command queues or returns error gracefully
Actual: Process dies, requires systemctl restart

Environment:
- OS: Ubuntu 22.04
- Java: OpenJDK 21
- Paper: 1.21.11 build 131
```

---

## ✨ Suggest a Feature

1. Check if already suggested in [discussions](../../discussions)
2. Create new discussion or issue
3. Describe the feature and why you need it
4. Provide examples/mockups if applicable

### Example Features We'd Love:
- [ ] Player whitelist management via Telegram
- [ ] Server stats dashboard
- [ ] Automatic world backup with version control
- [ ] Multi-language support
- [ ] Discord integration
- [ ] Web admin panel

---

## 🔧 Development Setup

### Prerequisites
```bash
# Clone repository
git clone https://github.com/YOU/minecraft-telegram-bot.git
cd minecraft-telegram-bot

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install dev dependencies
pip install -r requirements-dev.txt
```

### File Structure
```
.
├── src/
│   └── tg_bridge.py         # Main bot code
├── scripts/
│   ├── setup.sh             # Installation
│   └── backup.sh            # Backup script
├── templates/
│   └── .env.example         # Config template
├── docs/
│   └── *.md                 # Documentation
└── tests/                   # Unit tests (future)
```

---

## 💻 Code Style

### Python
```python
# Follow PEP 8
# Use 4-space indentation
# Add type hints where possible
# Document functions with docstrings

def cmd_backup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle /backup command - Create manual server backup.
    
    Args:
        update: Telegram update object
        context: Telegram context object
    """
    pass
```

### Bash
```bash
#!/bin/bash
set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Comment your code
SERVICE_NAME="${MINECRAFT_SERVICE:-minecraft}"

# Use functions for reusability
cleanup() {
    echo "Cleanup code here"
}
```

### Comments
```python
# Good: Explains WHY
# We use async for backups to prevent bot freezing
async def run_backup_job(bot):
    pass

# Bad: Explains WHAT (code already shows this)
# Create backup job
async def run_backup_job(bot):
    pass
```

---

## 🧪 Testing

### Before submitting PR:
```bash
# Run linting
pylint src/tg_bridge.py

# Type checking
mypy src/tg_bridge.py

# Manual testing on dev server
./scripts/setup.sh

# Test critical paths:
# 1. /backup command
# 2. /server restart
# 3. Chat message forwarding
# 4. Error handling
```

### Test Cases to Add:
- [ ] RCON connection failure handling
- [ ] Invalid .env configuration
- [ ] Telegram rate limiting
- [ ] Concurrent backup attempts
- [ ] Server startup timing

---

## 📝 Pull Request Process

### 1. Fork & Branch
```bash
git checkout -b feature/your-feature-name
```

### 2. Make Changes
```bash
# Edit files
git add .
git commit -m "feat: Add your feature description"

# Test everything works
./scripts/setup.sh
# Manual testing...
```

### 3. Push & Create PR
```bash
git push origin feature/your-feature-name
```

Then click "Create Pull Request" on GitHub

### 4. PR Description Template
```
## Description
What does this PR do?

## Type
- [ ] Bug fix
- [ ] New feature
- [ ] Improvement
- [ ] Documentation

## Testing
How did you test this?
- [ ] Manual testing on dev server
- [ ] Unit tests added
- [ ] Integration tested

## Checklist
- [ ] Code follows style guide
- [ ] Comments added for complex logic
- [ ] Documentation updated
- [ ] No breaking changes
- [ ] Tested with Python 3.8+
```

### 5. Review & Merge
- Address review comments
- Update PR as needed
- Maintainer merges when ready

---

## 📚 Documentation Contributions

### Fixing Typos
```bash
# Find the .md file
grep -r "typo" docs/

# Edit and create PR
```

### Adding Guides
Great ideas for new docs:
- [ ] Troubleshooting guide
- [ ] Performance tuning
- [ ] Security hardening
- [ ] Multi-server setup
- [ ] Video tutorials

---

## 🔐 Security Issues

**Do NOT** open a public issue for security vulnerabilities!

Instead:
1. Email: [security@example.com](mailto:security@example.com)
2. GPG key: [Available on website]
3. Include: Description, impact, reproduction steps
4. We'll respond within 48 hours

---

## 📋 Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation only
- `style:` Formatting, missing semicolons, etc
- `refactor:` Code restructuring
- `perf:` Performance improvement
- `test:` Adding tests
- `chore:` Dependency updates, etc

### Examples:
```bash
feat(bot): Add player whitelist management via Telegram
fix(backup): Handle rclone connection timeout gracefully
docs(readme): Update setup instructions for Ubuntu 24.04
refactor(rcon): Extract connection pooling logic
perf(logging): Reduce log file I/O with batching
```

---

## 🎯 Areas Needing Help

### High Priority
- [ ] Windows/WSL testing & documentation
- [ ] Docker containerization
- [ ] CI/CD pipeline setup
- [ ] Unit test coverage

### Medium Priority
- [ ] Performance optimization
- [ ] Additional language translations
- [ ] Web dashboard prototype
- [ ] Monitoring integration

### Nice to Have
- [ ] Pterodactyl panel integration
- [ ] Discord bot alternative
- [ ] Alternative database backends
- [ ] Mobile app (React Native)

---

## 🚀 Getting Your PR Merged

### Good PR Checklist
- ✅ Solves a real problem or adds useful feature
- ✅ Well-tested and documented
- ✅ Follows code style
- ✅ Clear commit messages
- ✅ No unnecessary dependencies
- ✅ Works on Python 3.8+
- ✅ Doesn't break existing functionality

### Will Be Rejected
- ❌ Solves non-existent problem
- ❌ Adds external dependencies without justification
- ❌ Breaks backward compatibility
- ❌ Has no tests
- ❌ Cluttered commit history
- ❌ Includes secrets/credentials

---

## 📞 Questions?

- **Discord:** [Join our server](https://discord.gg/example)
- **Discussions:** [GitHub Discussions](../../discussions)
- **Email:** [contact@example.com](mailto:contact@example.com)
- **Issues:** Use for bug reports and feature requests

---

## 🎉 Recognition

Contributors are recognized in:
1. **README.md** - Contributors section
2. **CHANGELOG.md** - Release notes
3. **GitHub** - Automatically as contributor

---

**Thank you for contributing! Every help makes this project better! 🙏**
