import json
import logging
from datetime import datetime

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat() + "Z",
            "level": record.levelname,
            "message": record.getMessage(),
        }
        
        # Add any extra arguments passed via logger.info("...", extra={})
        if hasattr(record, 'request_meta'):
            log_data.update(record.request_meta)
            
        if hasattr(record, 'llm_meta'):
            log_data.update(record.llm_meta)

        return json.dumps(log_data)
