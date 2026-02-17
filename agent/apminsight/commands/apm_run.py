import os
import sys
import time
import argparse
import shutil


debug = False

command_help = """
command : apminisght-run <options> <user application command>
Add options and user application startup commands as arguments
Examples
apminsight-run python app.py
apminsight-run --apm_app_name "monitorname" gunicorn myproject.wsgi
apminsight-run --apm_app_name "monitorname" --apm_log_dir "logs location" gunicorn myproject.wsgi
"""


def log(text, *args):
    if debug:
        currenttime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        print("APMINSIGH_PYTHON %s (%d) - %s" % (currenttime, os.getpid(), text % args))


def set_apm_config(args):
    debug = args.apm_debug or os.environ.get("APM_DEBUG", False)
    if debug:
        os.environ["APM_DEBUG"] = True

    if args.license_key:
        os.environ["S247_LICENSE_KEY"] = args.license_key
    if args.apm_app_name:
        os.environ["APM_APP_NAME"] = args.apm_app_name
    if args.apm_log_dir:
        os.environ["APM_LOGS_DIR"] = args.apm_log_dir
    if args.apm_exp_host:
        os.environ["APM_EXPORTER_HOST"] = args.apm_exp_host
    if args.apm_exp_status_port:
        os.environ["APM_EXPORTER_STATUS_PORT"] = args.apm_exp_status_port
    if args.apm_exp_data_port:
        os.environ["APM_EXPORTER_DATA_PORT"] = args.apm_exp_data_port

    if args.apm_monitor_group:
        os.environ["APMINSIGHT_MONITOR_GROUP"] = args.apm_monitor_group

    if args.apm_tags:
        os.environ["APMINSIGHT_TAGS"] = args.apm_tags

    os.environ["APMINSIGHT_INSTALL_DIR"] = os.path.dirname(__file__)
    os.environ["APMINSIGHT_RUN_COMMAND_DIR"] = os.getcwd()
    os.environ["APMINSIGHT_RUN_EXECUTABLE_COMMAND"] = " ".join(args.command) if args.command else None


def set_bootstrap_path(root_dir):

    bootstrap_dir = os.path.join(root_dir, "bootstrap")
    log("boot_directory = %r", bootstrap_dir)

    python_path = os.environ.get("PYTHONPATH", "")
    if "PYTHONPATH" in os.environ:
        python_path = "%s%s%s" % (bootstrap_dir, os.path.pathsep, os.environ["PYTHONPATH"])

    os.environ["PYTHONPATH"] = python_path if python_path else bootstrap_dir

    log("PYTHONPATH: %s", os.environ["PYTHONPATH"])
    log("sys.path: %s", sys.path)


def get_executable_path(executable_path):
    try:
        if os.path.isfile(executable_path):
            return executable_path

        if hasattr(shutil, "which"):
            return shutil.which(executable_path)
        else:
            from distutils import spawn

            return spawn.find_executable(executable_path)
    except Exception as exc:
        if not os.path.dirname(executable_path):
            program_search_path = os.environ.get("PATH", "").split(os.path.pathsep)
            for path in program_search_path:
                if os.path.exists(path) and os.access(path, os.X_OK):
                    path = os.path.join(path, executable_path)
                    executable_path = path
                    break
        return executable_path


def execute_startup_command(args):
    try:
        # check the python executable is available under os.path
        executable_path = get_executable_path(args.command[0])
        executable_args = args.command[1:]
        log("executable_arguments = %r", [executable_path] + executable_args)

        try:
            os.execl(executable_path, executable_path, *executable_args)
        except Exception as exc:
            print(
                "apminsight-run: error while executing the user command '%s' %s"
                % (executable_path % executable_args, str(exc))
            )
            raise
    except Exception:
        print(f'[ERROR] Failed to run Application with Startup command "{ " ".join(args.command)}"')
        print("[ERROR] check application is running with above command without apminsight")


def set_parser():

    parser = argparse.ArgumentParser(
        description=command_help, formatter_class=argparse.RawTextHelpFormatter, prog="apminsight"
    )

    parser.add_argument(
        "command",
        nargs=argparse.REMAINDER,
        type=str,
        help='provide Application startup Command \n Eg:\t"python3 manage.py runserver"\n\t"python3 flask_app.py"\n\t"gunicorn -b host:port myapp.wsgi:application"',
    )
    parser.add_argument("-lk", "--license_key", help=" Add apminsight license key")
    parser.add_argument("-apmname", "--apm_app_name", help="Add APM Insight application name")
    parser.add_argument("-ald", "--apm_log_dir", help="Add custom log directory for storing APM logs ")
    parser.add_argument("-ad", "--apm_debug", help="enable debug mode")
    parser.add_argument(
        "-aeh", "--apm_exp_host", help="Set apm exporter host to a remote machine or docker container host"
    )
    parser.add_argument("-aesp", "--apm_exp_status_port", help="Set apm exporter status port ")
    parser.add_argument("-aedp", "--apm_exp_data_port", help="Set apm exporter data port")
    parser.add_argument(
        "-amg",
        "--apm_monitor_group",
        help='Set apm monitor group as a string. \n Eg: -amg "Pro-app,Test,milestone group"',
    )
    parser.add_argument("-at", "--apm_tags", help='Set apm tags as a string \n Eg: -at "en:prod,version:1.0"')

    return parser


def main():
    global debug
    try:
        parser = set_parser()
        if len(sys.argv[1:]) == 0:
            print("[WARNING] Command args are not provided follow the below help")
            parser.print_help(sys.stderr)
            sys.exit(0)

        log("current_command = %r", sys.argv)

        root_dir = os.path.dirname(os.path.dirname(__file__))
        log("root_directory = %r", root_dir)

        # add boothstrap to python path
        set_bootstrap_path(root_dir)
        args = parser.parse_args()
        if not args.command:
            print("[ERROR] Application Startup command not provided")
            sys.exit(0)

        set_apm_config(args)
        execute_startup_command(args)

    except Exception as exc:
        print("apminsight-run: Error while executing the script '%s' %s" % (sys.argv, str(exc)))
        raise

    sys.exit(0)
