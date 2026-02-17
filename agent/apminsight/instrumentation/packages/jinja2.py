from apminsight import constants

module_info = {
    "jinja2.environment": [
        {
            constants.class_str: "Template",
            constants.method_str: "render",
            constants.component_str: constants.jinja_comp,
        },
        {
            constants.class_str: "Environment",
            constants.method_str: "compile",
            constants.component_str: constants.jinja_comp,
        },
    ]
}
