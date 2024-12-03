from google.cloud import logging 


class CloudLogger:

    def __init__(
            self,
            log_name: str,
            project_id: str = None
    ):
        self.client = logging.Client(project=project_id) if project_id else logging.Client()
        self.logger = self.client.logger(log_name)
        self.labels = dict()

    def debug(self, message):
        self.logger.log_text(message, severity='DEBUG', labels=self.labels)

    def info(self, message):
        self.logger.log_text(message, severity='INFO', labels=self.labels)

    def error(self, message):
        self.logger.log_text(message, severity='ERROR', labels=self.labels)

    def warning(self, message):
        self.logger.log_text(message, severity='WARNING', labels=self.labels)

    def set_label(self, label, value):
        self.labels[label] = value

    def log_struct(
            self,
            message: str,
            severity: str = 'INFO',
            **kwargs
    ):
        self.logger.log_struct({
            'message': f'{message} {{...}}',
            **kwargs
        },
            labels=self.labels,
            severity=severity
        )


def get_logger(name: str, project: str) -> CloudLogger:
    return CloudLogger(log_name=name, project_id=project)
