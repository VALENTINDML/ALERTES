from config.db import get_connection

try:
    conn = get_connection()
    print("Connexion OK")
    conn.close()

except Exception as e:
    print(e)