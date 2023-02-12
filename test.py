import bot

bot.main()

with open("token.txt", "r") as f:
    TOKEN = f.read().strip().split("\n")[0]
