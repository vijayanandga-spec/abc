
#!/bin/bash

if [ "x${S247_LICENSE_KEY}" = "x" ]; then
        echo  "Site24x7 License key is not provided, terminating the process  "
        exit 1
fi

if [ "x${APP_RUN_COMMAND}" = "x" ]; then
        echo  "APP_RUN_COMMAND must be set. So Aborting..."
        exit 1
fi

#  wget -O InstallDataExporter.sh https://staticdownloads.site24x7.com/apminsight/S247DataExporter/linux/InstallDataExporter.sh

if [ -n "$APP_ENV_PATH" ]; then
        APPLICATION_DIR=$(pwd)
        cd $APP_ENV_PATH && \
        . "$(pwd)/activate" && \
        cd $APPLICATION_DIR

        if [ $? -ne 0 ]; then
                echo "Error: Failed to activate the virtual environment. $APP_ENV_PATH"
                echo " Please provide virtual environment path till bin folder of your environment"
                exit 1  # Exit the script with an error status
        else
                echo "Activated Virtual environment successfully at $APP_ENV_PATH"
        fi
fi


SCRIPT_PATH="$(cd "$(dirname "$0")" && pwd)"
echo "SCRIPT RUN PATH : $SCRIPT_PATH"

## Setting env for locating APM Python module location
export APM_MODULE_PATH="$SCRIPT_PATH"
echo "APM MODULE PATH : $APM_MODULE_PATH"

WORKING_DIR=$(pwd)
cd $SCRIPT_PATH

## Setting PYTHONPATH Variable for module loading during runtime
PY_PATH="$PYTHONPATH"
NEW_PATH="$(pwd)/wheels/apminsight/bootstrap:$(pwd)/wheels/"
export PYTHONPATH="$NEW_PATH:$PY_PATH"
echo "PYTHONPATH : $PYTHONPATH"

if [ -z "$APM_INSTALLATION_PATH" ]; then
        echo "Installing DataExporter in folder $SCRIPT_PATH"
        Exporter="exporter"
        mkdir -p $Exporter
        cp -r S247DataExporter $Exporter
        # ls -lR exporter
        exporter/S247DataExporter/bin/S247DataExporter run &

else
        echo "Installing DataExporter in: $APM_INSTALLATION_PATH"
        mkdir -p $APM_INSTALLATION_PATH

        if [ -z "$APM_LOGS_DIR" ]; then
                export APM_LOGS_DIR="$APM_INSTALLATION_PATH"
        fi

        cp -r S247DataExporter $APM_INSTALLATION_PATH
        cd $APM_INSTALLATION_PATH
        S247DataExporter/bin/S247DataExporter run &

fi


for pid in /proc/[0-9]*/cmdline; do
    if [ -f "$pid" ]; then
        echo -n "PID: $(basename "$(dirname "$pid")") "
        tr -d '\0' < "$pid" | awk '{print "Process Name:",$0}'
    fi
done

cd $WORKING_DIR

$APP_RUN_COMMAND

