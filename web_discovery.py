#!/usr/bin/env python

# Written by Brad Beltman  @bradbeltman

import subprocess
import argparse
from socket import gethostbyname, gaierror
from os import path, mkdir, error
from sys import exit, stdout
from urlparse import urlparse


class Colors:
    # This class adds colored text
        header = '\033[95m'
        blue = '\033[94m'
        green = '\033[92m'
        warning = '\033[93m'
        fail = '\033[91m'
        endc = '\033[0m'
        bold = '\033[1m'
        underline = '\033[4m'


def get_target(my_target):
    # This function parses the target variable and creates a named list of the URL parts
    parsed_url = urlparse(my_target)
    if parsed_url.scheme is None or parsed_url.hostname is None:  # This should never happen, but just in case
        print(Colors.fail + "\nThe URL is malformed, exiting!\n" + Colors.endc)
        exit(1)
    return parsed_url


def resolve_host(my_hostname):
    # This function attempts to resolve the hostname before continuing with the scan.  Supplying an IP address will
    # always return true and the script will continue
    try:
        gethostbyname(my_hostname)  # If the address resolves, continue with the script
    except gaierror:
        print(Colors.fail + "\nCan't resolve " + my_hostname + ", check it and try again. Exiting!\n" + Colors.endc)
        exit(1)  # Don't run any processes if cannot resolve the host, troubleshoot first


def call_interrupt(process_name):
    # This function prompts the user if ctrl-c is hit during subprocess execution
    print(Colors.warning + "\n" + process_name + " has been killed!\n" + Colors.endc)
    while True:
        my_prompt = raw_input("Continue (c) or Abort (a) remaining processes?  c/a ")
        if my_prompt == "" or my_prompt.lower() == 'c':  # Continue by default
            print("\nContinuing\n")
            return
        elif my_prompt.lower() == "a":  # Abort all processes
            print("\nAborting all processes!  Goodbye\n")
            exit(1)
        else:  # Re-prompt if user doesn't enter c, a, or a blank response
            print(Colors.warning + "\nI don't know what you mean, try again!\n" + Colors.endc)
            pass


def dir_exists(dir_check):
    # Check if the specified directory already exists
    if path.isdir(dir_check):
        pass  # Continue if the directory already exists
    else:
        mkdir(dir_check)  # Create the directory if it doesn't already exist.


def write_file(my_dir, my_hostname, process_name, file_contents):
    # Write output to files if an output directory was specified
    if file_contents is None:  # If a command fails and there is no output, continue running other tools
        return
    dir_exists(my_dir)  # Call the function to check if the directory exists, and create it if not
    hostname = my_hostname.replace('.', '-')  # Replace dots so as to not confuse the extension
    file_name = hostname + "_" + process_name + ".txt"  # Friendly filename, with a .txt extension
    file_location = my_dir + "/" + file_name  # Set the relative path
    try:
        with open(file_location, 'w') as o:  # Open the file with write permissions
            o.write(file_contents)  # Write the process output to file
    except error:  # If there's an error writing the file, inform the user
        print(Colors.warning + "\nThere was a problem writing the file, not output will be written!\n" + Colors.endc)


def check_target():
    #  Do some prelim checks and queue up each target
    if targ.startswith("http"):  # Check that the scheme specified so we know how to call each process
        this_target = get_target(targ)  # Send to a function to parse the URL, returns named list
        resolve_host(this_target.hostname)  # Verify we can resolve the target name before running anything against it
        if this_target.scheme == 'http' and 'sslscan' in args.process_list:  # Skip sslscan if no https
            print(Colors.warning + "\nsslscan will be skipped because https is not in use!\n" + Colors.endc)
            args.process_list.remove('sslscan')
        for p in args.process_list:  # Iterate through the list of processes to run
            call_process(p, this_target, args.out_dir, args.proxy)  # Call the function to actually execute the process
    else:  # If the scheme was not specified, print an error
        print(Colors.fail + "\nYou need to specify http or https, I'm skipping " + targ + "\n" + Colors.endc)
        pass  # Continue the loop, so entries that specify the scheme can still run


def call_process(my_process, my_target, output_dir, my_proxy):
    # This function calls each process, and displays output in real time. Add processes as needed below

    # Specify nmap command structure
    if my_process == 'nmap':
        process_command = [my_process, "-Pn", "-A", my_target.hostname]

    # Specify sslscan command structure
    elif my_process == 'sslscan':
        process_command = [my_process, my_target.netloc]

    # Specify Nikto command structure
    elif my_process == 'nikto':
        process_command = [my_process, "-h", my_target.scheme + "://" + my_target.netloc]
        if my_target.scheme == "https":
            process_command.append("-ssl")  # Not strictly necessary, but will speed up testing according to the docs
        if my_proxy is not None:  # Add a proxy if one is specified
            process_command.extend(["-useproxy", my_proxy])

    # Specify dirb command structure
    elif my_process == 'dirb':
        if my_target.path is not None:
            process_command = [my_process, my_target.scheme + "://" + my_target.netloc + "/" + my_target.path, "-S", "-w"]
        else:
            process_command = [my_process, my_target.scheme + "://" + my_target.netloc, "-S", "-w"]
        if my_proxy is not None:
            process_command.extend(["-p", my_proxy])

    else:  # For any commands we don't have handled above, print a message and move on
        print(Colors.warning + "\nI don't know what to do with " + my_process + ".  I'll skip it!\n" + Colors.endc)
        return
    print(Colors.blue + "Running: " + ' '.join(process_command) + "\n" + Colors.endc)
    try:
        try:
            process_output = ""
            process_results = subprocess.Popen(process_command, stdout=subprocess.PIPE)
            for c in iter(lambda: process_results.stdout.read(1), ''):  # Capture results in real-time
                stdout.write(c)  # Write output to screen as it comes in, so we can see real-time results
                if output_dir is not None:
                    process_output += str(c)  # Add to variable so we can write all to file
            if output_dir:  # If an output directory was specified, write output to files there
                write_file(output_dir, my_target.hostname, my_process, process_output)
            print(Colors.green + "\n" + my_process + " ran successfully!\n" + Colors.endc)
        except subprocess:  # If there's a problem running a process, inform the user
            print(Colors.warning + "There was a problem running "
                  + my_process + "!  I will continue with the next process" + Colors.endc)
            pass
    except KeyboardInterrupt:  # Capture ctrl+c (which will kill the current process) and prompt the user
        call_interrupt(my_process)


# Parse arguments from the command line
parser = argparse.ArgumentParser(description="Run basic info gathering apps against a web target")
parser.add_argument('-t', dest='target', help='A target URL.  E.X. https://www.example.com')
parser.add_argument('-T', dest='targets', help='Specify a file with a list of targets, one per line')
parser.add_argument('-r', dest='process_list', nargs='+', default=['nmap', 'sslscan', 'nikto', 'dirb'],
                    help='Specify apps to run.  E.X. -r nmap nikto dirb')
parser.add_argument('-o', dest='out_dir', help='Specify an output directory. If none given, output to the screen only')
parser.add_argument('-x',   dest='proxy',   help='Proxy to send HTTP traffic through')

args = parser.parse_args()

target = []  # Initialize a list to hold each target

try:
    if args.targets is not None:  # If specifying a list of targets using -T
        if path.isfile(args.targets):  # Verify the file actually exists
            with open(args.targets, 'r') as f:  # Open file in read mode
                for t in f:  # Read each line of the file, and append it to a list
                    target.append(t.strip())  # Strip newline chars from the end of each line
        else:  # If the file does not exist, print error and exit.
            print(Colors.fail + "\nThe file you specified does not exist, exiting!\n" + Colors.endc)
            exit(1)
    else:  # Append just the single target using -t
        target.append(args.target)

    for targ in target:  # Iterate over each target in the list
        check_target()
    print("\nAll processes finished!\n")  # Once all processes have been run against all targets, inform the user
except KeyboardInterrupt:  # Capture ctrl+c to prevent nasty error messages
    print("\nQuitting!\n")
    exit(1)
