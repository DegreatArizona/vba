import subprocess
import os

def handler(req, res):
    try:
        # Run the Django management command
        result = subprocess.run(
            ['python', 'manage.py', 'remove_expired_subscriptions'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Capture the output and errors
        output = result.stdout.decode('utf-8')
        errors = result.stderr.decode('utf-8')

        # Check the return code
        if result.returncode == 0:
            # Return success response with output
            res.status(200).send(f"Success: {output}")
        else:
            # Return error response with the error message
            res.status(500).send(f"Error: {errors}")
    
    except subprocess.CalledProcessError as e:
        # Handle command-specific errors
        res.status(500).send(f"Error executing cron job: {str(e)}")
    
    except Exception as e:
        # Handle any other exceptions
        res.status(500).send(f"General Error: {str(e)}")
    
    return res
