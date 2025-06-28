# Bot Deployment Guide

## 🗄️ Database Configuration

The bot now supports multiple database configurations:

### **For Deployment (Railway/Heroku/etc.):**
- **Railway MySQL**: Automatically detected and used when available
- **Environment Variables**: Can be set for custom MySQL connections
- **Fallback**: SQLite if no MySQL connection is available

### **For Local Development:**
- **Local MySQL**: If available and configured
- **SQLite**: Automatic fallback if MySQL is not available

## 🚀 Deployment Steps

### **Option 1: Railway (Recommended)**
1. Connect your GitHub repository to Railway
2. Set environment variables:
   ```
   DISCORD_TOKEN=your-discord-bot-token
   ```
3. Deploy! The bot will automatically use Railway MySQL

### **Option 2: Heroku**
1. Create a Heroku app
2. Add MySQL addon (ClearDB, JawsDB, etc.)
3. Set environment variables:
   ```
   DISCORD_TOKEN=your-discord-bot-token
   MYSQL_HOST=your-mysql-host
   MYSQL_PORT=3306
   MYSQL_USER=your-mysql-user
   MYSQL_PASSWORD=your-mysql-password
   MYSQL_DATABASE=your-mysql-database
   ```
4. Deploy!

### **Option 3: Other Platforms**
Set the same environment variables as Heroku for any platform that supports MySQL.

## 🔧 Local Development

### **With MySQL:**
```powershell
$env:DISCORD_TOKEN = "your-discord-bot-token"
$env:MYSQL_HOST = "localhost"
$env:MYSQL_USER = "root"
$env:MYSQL_PASSWORD = "your-password"
$env:MYSQL_DATABASE = "botdb"
python main.py
```

### **Without MySQL (SQLite fallback):**
```powershell
$env:DISCORD_TOKEN = "your-discord-bot-token"
python main.py
```

## 📊 Database Priority

The bot tries databases in this order:
1. **Railway MySQL** (if available)
2. **Local MySQL** (if environment variables set)
3. **SQLite** (fallback)

## ✅ Available Commands

Once deployed and running:
- `dm.set_mode <definition|tournament|both>` - Set bot mode
- `dm.help tournament` - Tournament system help
- `dm.help definitions` - Definitions system help
- `dm.help` - General help

## 🔒 Security Notes

- Never commit your Discord token to Git
- Use environment variables for all sensitive data
- Railway MySQL credentials are already configured for deployment 