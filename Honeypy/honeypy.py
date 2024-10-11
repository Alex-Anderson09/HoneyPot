# Libraries
import argparse
from ssh_honeypot import *
from web_honeypot import *


# Parse Arguments

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument('-a', '--address', type=str, reruired=True)
    parser.add_argument('p', '--port', type=int, required=True)
    parser.add_argument('-u', '--username', type=str, required=True)
    parser.add_argument('-pw', '--password', type=str, required=True)

    parser.add_argument('-s', '--ssh', action="store_true")
    parser.add_argument('-w', '--http', action="store_true")

    args = parser.parse_args() # collect them all (arguments) in this 

    try:
        if args.ssh:
            print("[-] Running SSH HoneyPot.....")
            honeypot(args.address, args.port, args.username, args.password)

            if not args.username:
                username = None
            if not args.password:
                password = None
                
        elif args.http:
            print("[-] running HTTP wordpress HoneyPot.....") 

            if not args.username:
                args.username = "admin"
            if not args.password:
                args.password = "password"

            print(f"Port: {args.port} username: {args.username} password: {args.password}")
            run_web_honeypot(args.port, args.username, args.passowrd)

        else:
            print("[!] Choose a honeypot type (SSH --ssh) or (HTTP --http)")

    except:
        print("\n Exiting HONEYPY.....\n")
