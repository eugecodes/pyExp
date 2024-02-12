from config.settings.base import TestBaseSettings


class Settings(TestBaseSettings):
    DEBUG: bool = True
    SECRET_KEY: str = "Dummy-Secret-KEY"
    # Mail settings
    EMAIL_MODE = "SNMP"
    EMAIL_CONFIG_USERNAME: str = ""
    EMAIL_CONFIG_PASSWORD: str = ""
    EMAIL_CONFIG_FROM: str = "root@localhost.com"
    EMAIL_CONFIG_PORT: str = "1025"
    EMAIL_CONFIG_SERVER: str = "mailhog"
    EMAIL_CONFIG_FROM_NAME: str = "root@localhost.com"
    EMAIL_CONFIG_STARTTLS: bool = False
    EMAIL_CONFIG_SSL_TLS: bool = False
    EMAIL_CONFIG_USE_CREDENTIALS: bool = True
    EMAIL_CONFIG_VALIDATE_CERTS: bool = True
    EMAIL_CONFIG_TEMPLATE_FOLDER: str = "src/templates/email"
    EMAIL_CONFIG_SUPPRESS_SEND: int = 0
    SENDIN_BLUE_API_KEY: str = "API-KEY"
    # End email settings
