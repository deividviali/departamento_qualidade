# gera senha hash
from werkzeug.security import generate_password_hash
print(generate_password_hash("123456"))


# from sqlalchemy import create_engine, text

# DB_HOST_EXT = "172.16.139.20"
# DB_PORT_EXT = 33061
# DB_USER_EXT = "app.suporte.dinfo"
# DB_PASS_EXT = "5hjnk4Ji&z%&"
# DB_NAME_EXT = "siga-homo83"  

# engine_extern = create_engine(
#     f"mysql+pymysql://{DB_USER_EXT}:{DB_PASS_EXT}@{DB_HOST_EXT}:{DB_PORT_EXT}/{DB_NAME_EXT}"
# )

# with engine_extern.connect() as conn:
#     result = conn.execute(text("SELECT * FROM vw_aplicacao_suporte LIMIT 5"))
#     for row in result:
#         print(row)

