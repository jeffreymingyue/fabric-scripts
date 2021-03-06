from fabric.api import *
from fabric.utils import error
import re

@task
def uptime():
    """Show uptime and load"""
    run('uptime')

@task
def free():
    """Show memory stats"""
    run('free')

@task
def disk():
    """Show disk usage"""
    run('df -kh')

@task
def os_version():
    """Show operating system"""
    run('facter lsbdistcodename lsbdistdescription operatingsystem operatingsystemrelease')

@task
def deprecated_library(name):
    """
    Find processes that are using a deprecated library and need restarting

    For example:
      - Processes using a non-upgraded version of libssl:
        vm.deprecated_library:libssl

      - Processes that are using any deleted/upgraded library:
        vm.deprecated_library:/lib
    """
    sudo("lsof -d DEL | awk '$8 ~ /{0}/'".format(re.escape(name)))

@task
def stopped_jobs():
    """Find stopped govuk application jobs"""
    with hide('running'):
        run('grep -l govuk_spinup /etc/init/*.conf | xargs -n1 basename | while read line; do sudo status "${line%%.conf}"; done | grep stop || :')

@task
def bodge_unicorn(name):
    """
    Manually kill off (and restart) unicorn processes by name

    e.g. To kill off and restart contentapi on backend-1 in Preview:

      fab preview -H backend-1.backend vm.bodge_unicorn:contentapi

    ...or on all backend hosts in Preview:

      fab preview class:backend vm.bodge_unicorn:contentapi

    Yes. This is a bodge. Sorry.
    """
    pid = run("ps auxwww | grep '/%s/' | grep -F 'unicorn master' | grep -v grep | awk '{ print $2 }' | xargs" % name)
    if pid:
        sudo("kill -9 %s" % pid)
    sudo("start '{0}' || restart '{0}'".format(name))

@task
def reload_unicorn(name):
    error("task deprecated by 'app.reload'")

def reboot_required():
    """
    Check whether a reboot is required

    """
    result = run("/usr/local/bin/check_reboot_required 30 0", warn_only=True)
    return (not result.succeeded)

@task
def reboot():
  """Schedule a host for downtime in nagios and reboot (if required)

  Usage:
  fab production -H frontend-1.frontend.production vm.reboot
  """
  if reboot_required():
      # we need to ensure we only execute this task on the current
      # host we're operating on, not every host in env.hosts
      execute(force_reboot, hosts=[env['host_string']])

@task
def force_reboot():
  """Schedule a host for downtime in nagios and force reboot (even if not required)"""
  from nagios import schedule_downtime
  execute(schedule_downtime, env['host_string'])
  run("sudo shutdown -r now")

@task
def poweroff():
  """Schedule a host for downtime in nagios and shutdown the VM

  Usage:
  fab production -H frontend-1.frontend.production vm.poweroff
  """
  from nagios import schedule_downtime
  execute(schedule_downtime, env['host_string'])
  run("sudo poweroff")

@task
@hosts('puppetmaster-1.management')
def host_key(hostname):
  """
  Check the SSH host key of a machine. This task runs on the Puppetmaster because
  it's the only machine that knows about all host keys.

  Usage:
  fab production vm.host_key:backend-1.backend
  """
  with hide('running', 'stdout'):
    ssh_key = run("grep {0} /etc/ssh/ssh_known_hosts | head -1".format(hostname))

  if ssh_key == '':
    print 'Machine {0} not found in ssh_known_hosts file'.format(hostname)
  else:
    with hide('running'):
      run("ssh-keygen -l -f /dev/stdin <<< '{0}'".format(ssh_key))
