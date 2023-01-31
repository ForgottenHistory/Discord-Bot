admin_users = []
with open('admin_users.txt', 'r') as file:
    admin_users = file.readlines()


admin_users = [line.strip() for line in admin_users]

print(admin_users)
x = input()
