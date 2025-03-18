import wandb
from fairops.mlops.autolog import LoggerFactory


wb_logger = LoggerFactory.get_logger("wandb")
wb_logger.log_metric("loss", 0.05)
print("W&B Logged Metrics:", wb_logger.logged_metrics)
