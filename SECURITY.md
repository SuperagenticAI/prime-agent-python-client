# Security policy

Please report vulnerabilities privately through GitHub's security advisory
form for this repository. Do not open a public issue containing exploit details
or credentials.

This package launches Prime Agent and communicates with it over local standard
input and output. It does not sandbox Prime Agent, the selected model, project
commands, extensions, or generated Python. Applications are responsible for
choosing an appropriate operating-system or container boundary.

Supported security fixes are released for the latest minor version.

