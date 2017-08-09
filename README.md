# web_discovery
Run basic discovery/scanning tools against a web target

Arguments:

-t  specify a single target.  e.x. http://www.target-org.com/app

-T  give it a file with a list of targets

-r  specify which tools to run.  Default: nmap sslscan nikto dirb

-o  specify a directory to save output under

-x  use a proxy for those tools which can use a proxy (HTTP proxy)

TODO:
1. Implement multiprocessing, so multiple instances can be run when more than one target is specified
2. Add ability to run with multiple wordlists for dirb (currently just uses the default common.txt file)
