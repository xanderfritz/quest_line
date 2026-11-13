# allow pymysql as a fallback driver when mysqlclient isnt available
try:
    import MySQLdb  # noqa: F401
except ImportError:
    import pymysql
    pymysql.install_as_MySQLdb()
