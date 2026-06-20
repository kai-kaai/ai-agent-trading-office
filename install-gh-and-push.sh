#!/bin/bash

set -e

echo "🚀 เริ่มติดตั้ง GitHub CLI และ push โปรเจค AI Agent Trading Office"

# ตรวจสอบและติดตั้ง Homebrew
if ! command -v brew &> /dev/null; then
    echo "📦 กำลังติดตั้ง Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    
    # เพิ่ม brew ไปยัง PATH (Apple Silicon / Intel)
    if [[ -f "/opt/homebrew/bin/brew" ]]; then
        eval "$(/opt/homebrew/bin/brew shellenv)"
    elif [[ -f "/usr/local/bin/brew" ]]; then
        eval "$(/usr/local/bin/brew shellenv)"
    fi
else
    echo "✅ Homebrew ติดตั้งอยู่แล้ว"
fi

# ติดตั้ง gh
if ! command -v gh &> /dev/null; then
    echo "📦 กำลังติดตั้ง GitHub CLI (gh)..."
    brew install gh
else
    echo "✅ GitHub CLI ติดตั้งอยู่แล้ว"
fi

# Login GitHub
echo ""
echo "🔑 กรุณา login GitHub (จะเปิด browser)"
gh auth login --hostname github.com --git-protocol ssh

# ตรวจสอบว่า login สำเร็จ
if ! gh auth status &> /dev/null; then
    echo "❌ Login ไม่สำเร็จ กรุณาลองใหม่"
    exit 1
fi

echo "✅ Login สำเร็จ"

# ตั้งค่าชื่อ repo
REPO_NAME="ai-agent-trading-office"
PROJECT_DIR="/Users/kaaimac/Desktop/AI Agent trading Office"

cd "$PROJECT_DIR"

# สร้าง repository บน GitHub (ถ้ายังไม่มี)
echo "📁 กำลังสร้าง repository บน GitHub..."
if gh repo view "$REPO_NAME" &> /dev/null; then
    echo "✅ Repository มีอยู่แล้ว"
else
    gh repo create "$REPO_NAME" --public --source=. --remote=origin --push
    echo "✅ สร้าง repository และ push สำเร็จ"
fi

# Push โค้ด (กรณีที่มีการเปลี่ยนแปลง)
echo "📤 กำลัง push โค้ด..."
git push -u origin main || git push

echo ""
echo "🎉 เสร็จสิ้น! Repository อยู่ที่: https://github.com/$(gh api user --jq .login)/$REPO_NAME"
echo "🔗 เปิดได้ที่: https://github.com/$(gh api user --jq .login)/$REPO_NAME"