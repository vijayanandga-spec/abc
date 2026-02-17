Site24x7 Python Application Performance Monitoring
=========================================

Monitor and optimize the performance of your Python application with the Site24x7 APM Insight Python agent. The agent provides you with information on the response time, throughput, database operations, and errors of your application. Keep track of these metrics over time to identify where they can be improved for better performance.

Make sure you have a Site24x7 account before you use an APM Insight agent to monitor metrics.

Requirements: Python version 3.7.0 and above.

Supported frameworks: Bottle, CherryPy, Django, Flask, and Pyramid.

Supported databases and components: PyMySQL, Psycopg2, Pymemcache, Redis, SQLite, Cassandra, Jinja2, Genshi, and Mako.

Supported HTTP libraries: http.client, httplib2, httpx, urllib, urllib3.

**S247DataExporter**

    The S247DataExporter is an independent process dedicated for communicating application metrics and traces to the Site24x7 server.

**Installation instructions for S247DataExporter:**

* Run the following commands in your terminal

        wget -O "InstallDataExporter.sh" https://staticdownloads.site24x7.com/apminsight/S247DataExporter/linux/InstallDataExporter.sh
        sudo sh InstallDataExporter.sh install -lk <S247_LICENSE_KEY>

* If you are using proxy, add the following snippet to the command 'sudo sh InstallDataExporter.sh install -lk <S247_LICENSE_KEY>'
       
        -pau <Proxy auth username> -pap <Proxy auth password> -psh <Proxy server host:Proxy server port>  -psph <Boolean value whether to use HTTPS protocol for proxy> -bp <Bollean value whether to use proxy or not>


  > *Note: By default, S247DataExporter uses 20021 as the AGENT STATUS PORT and 20022 as the AGENT DATA PORT. 

If you want to run the S247DataExporter in different ports, add the below configurations to the above mentioned command.

| Option | Description  |
| ------ | ------ |
| '-asp <Agent Status Port>' | To configure the custom Exporter Status Port |
| '-adp <Agent Data Port>' | To configure the custom Exporter Data Port |
| '-sld <Directory path>' | To log the Exporter logs to a custom directory |
| '-sll <Log level>' | To configure the Log level of Exporter logs |
| '-sls <Exporter log size>' | To configure the Exporter Log file size |

**Installation instructions for the S247 Python agent:**

If you are using a virtual environment, activate the virtual environment and run the following command to install the S247 APMINSIGHT Python package into your virtual environment

        pip install apminsight

**Integrate the Python agent to your application**
        
* *Using the command line* \
   You can use the below command for adding extra configurations:

        $ apminsight-run -lk "license_key" <apm-options> <user application execute command> 

| apm-options | Description |
| ------ | ------ |
| -lk, --license_key | To add the site24x7 license key or device key |
| -apmname, --apm_app_name | To add the APM application name |
| -ald, --apm_log_dir | To add a custom log directory for storing APM logs |
| -ad, --apm_debug | To enable debug mode |
| -aeh, --apm_exp_host | To configure the S247DataExporter host |
| -aesp, --apm_exp_status_port | To configure the S247DataExporter status port |
| -aedp, --apm_exp_data_port | To configure the S247DataExporter data port |

Examples:
 If you want to configure the application name, use the below command:

      apminsight-run --apm_app_name "monitorname" <user application execute command> 

  If you want to configure the directory location, use the below command:

      apminsight-run --apm_app_name "monitorname" --apm_log_dir "logs location" <user application execute command> 

* *Using the code snippet*
  > Note: Update the configuration in the code snippet below and place it at the top of your application route file or application start file.

        
        from apminsight import initialize_agent
        initialize_agent({
            "appname" : "<Your application name>",
            "license_key" : "< your site24x7 license key>",
            '''change if  S247DataExporter is not running in the default ports(20021, 20022):'''
            "exporter_status_port" : "<S247DataExporter status port>",
            "exporter_data_port" : "<S247DataExporter data port>",

            '''If you are running S247DataExporter on a separate machine/server or as a Docker container:'''
            "exporter_host" : "<HostName/ContainerName where S247DataExporter is running>"
        })

  For example, for Django applications, add the code snippet at the top of the Django settings.py file. The name of your Django application will be automatically detected by your WSGI_APPLICATION in the application's settings.py.

  For other applications and frameworks, such as Flask, add the code snippet at the top of the application start file.


* *Configure the agent using environment variables*

| Configuration | Description |
| ------ | ------ |
| $ export S247_LICENSE_KEY=< license key > | To add your site2x7 License or Device key |
| $ export APM_APP_NAME=<Your application name > | To add the APM application name |
| $ export APM_LOGS_DIR=< logs storing path > | To configure the log directory |
| $ export APM_EXPORTER_STATUS_PORT=< S247DataExporter status port >,
$ export APM_EXPORTER_DATA_PORT=< S247DataExporter data port > | To change the S247DataExporter's default running ports (20021, 20022) |
| $ export APM_EXPORTER_HOST=< HostName/ContainerName where S247DataExporter is running > | To change the host of the S247DataExporter to a different machine or server or as a Docker container |

* Restart your WSGI application and Perform some transactions so that the agent can collect data.
* Log in to your Site24x7 account.
* Navigate to APM Insight and click your application to view application metrics.
* You can view agent log files in the apminsightdata/logs directory, which will be present in the process-generated location.

