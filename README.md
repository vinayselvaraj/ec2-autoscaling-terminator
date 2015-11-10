# ec2-autoscaling-terminator

This is a AWS Lambda function written in Python that can terminate instances in an autoscaling group at set intervals.  The Lambda function can be configured to be invoked at set intervals using the 'Scheduled Event' event source.  The function will need an IAM role that has permissions to describe and terminate autoscaling groups.
