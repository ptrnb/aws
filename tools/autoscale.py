class LaunchCFG():
    """Create a launchconfig for the web layer"""

    def __init__(self):
        """hard code the launch configuration for now"""

        httpd_user_data = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            RESOURCES_DIRECTORY,
            'httpd_user_data.sh')

        with open(httpd_user_data, 'r') as user_data_file:
            user_data = user_data_file.read()

        launch_args_data = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            RESOURCES_DIRECTORY,
            'launch_config.yaml')

        with open(launch_args_data, 'r') as launch_args_file:
            launch_args = yaml.safe_load(launch_args_file)

        launch_args['UserData'] = user_data

        asc = boto3.client('autoscaling')
        asc.create_launch_configuration(**launch_args)
