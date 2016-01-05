#!/usr/bin/python3
# -*- coding: utf-8 -*-

# This command updates all or some of the installed subuser images.
try:
  import pathConfig
except ImportError:
  pass
#external imports
import sys
import optparse
#internal imports
import subuserlib.commandLineArguments
from subuserlib.classes.user import User
import subuserlib.update
import subuserlib.profile
from subuserlib.classes.permissionsAccepters.acceptPermissionsAtCLI import AcceptPermissionsAtCLI

#####################################################################################

def parseCliArgs(realArgs):
  usage = "usage: subuser update [options]"
  description = """Update subuser images.

  all
      Updates all subuser images which have been marked as out of date.

  EXAMPLE:
    $ subuser update all

  subusers
      Updates the specified subusers

  EXAMPLE:
    $ subuser update subusers iceweasel git

  lock-subuser-to SUBUSER GIT-COMMIT
      Don't want a subuser to be updated?  No problem, lock it to a given version with this update sub-command.  Use subuser update log to see a list of possible hashes.

  unlock-subuser SUBUSER
      Unlock the subuser and ensure that it is up-to-date.

"""
  parser=optparse.OptionParser(usage=usage,description=description,formatter=subuserlib.commandLineArguments.HelpFormatterThatDoesntReformatDescription())
  parser.add_option("--accept",dest="accept",action="store_true",default=False,help="Accept permissions without asking.")
  parser.add_option("--prompt",dest="prompt",action="store_true",default=False,help="Prompt before installing new images.")
  return parser.parse_args(args=realArgs)

#################################################################################################

@subuserlib.profile.do_cprofile
def update(realArgs):
  """
  Update your subuser installation.

  Old images are not deleted so that update lock-subuser-to and update rollback still work. In this example, dependency1 stays installed.

  Now we lock the dependent subuser and try changing it again.

  >>> update.update(["lock-subuser-to","dependent","HEAD"])
  Locking subuser dependent to commit: HEAD
  Verifying subuser configuration.
  Verifying registry consistency...
  Unregistering any non-existant installed images.
  Running garbage collector on temporary repositories...

  >>> with open("/home/travis/remote-test-repo/images/intermediary/image/SubuserImagefile",mode="w") as subuserImagefile:
  ...   _ = subuserImagefile.write("FROM-SUBUSER-IMAGE dependency3")

  And commit the changes to git.

  >>> repo1.run(["commit","-a","-m","changed dependency for intermediate from dependency2 to dependency3"])
  0

  Running an update after a change does nothing because the affected subuser is locked.

  >>> update.update(["all","--accept"])
  Updating...
  Updated repository file:///home/travis/remote-test-repo
  Verifying subuser configuration.
  Verifying registry consistency...
  Unregistering any non-existant installed images.
  Checking if images need to be updated or installed...
  Checking if subuser foo is up to date.
  Checking for updates to: foo@default
  Running garbage collector on temporary repositories...

  >>> user = User()
  >>> set(user.getRegistry().getSubusers().keys()) == set(['dependent', u'foo'])
  True

  >>> set([i.getImageSourceName() for i in user.getInstalledImages().values()]) == set([u'foo', u'dependency1', u'bar', u'dependent', u'intermediary', u'intermediary', u'dependency2', u'dependent'])
  True

  When we unlock the subuser it gets updated imediately.

  >>> update.update(["unlock-subuser","--accept","dependent"])
  Unlocking subuser dependent
  Verifying subuser configuration.
  Verifying registry consistency...
  Unregistering any non-existant installed images.
  Checking if images need to be updated or installed...
  Checking if subuser dependent is up to date.
  New images for the following subusers need to be installed:
  dependent
  Installing dependency3 ...
  Building...
  Building...
  Building...
  Successfully built 28
  Building...
  Building...
  Building...
  Successfully built 29
  Installing intermediary ...
  Building...
  Building...
  Building...
  Successfully built 30
  Building...
  Building...
  Building...
  Successfully built 31
  Installing dependent ...
  Building...
  Building...
  Building...
  Successfully built 32
  Building...
  Building...
  Building...
  Successfully built 33
  Installed new image <33> for subuser dependent
  Running garbage collector on temporary repositories...

  >>> user = User()
  >>> set(user.getRegistry().getSubusers().keys()) == set(['dependent', u'foo'])
  True

  >>> set([i.getImageSourceName() for i in user.getInstalledImages().values()]) == set([u'foo', u'dependency1', u'bar', u'dependent', u'intermediary', u'intermediary', u'dependency2',u'dependency3', u'dependent'])
  True
  """
  options,args = parseCliArgs(realArgs)
  user = User()
  permissionsAccepter = AcceptPermissionsAtCLI(user,alwaysAccept = options.accept)
  if len(args) < 1:
    sys.exit("No arguments given. Please use subuser update -h for help.")
  elif ["all"] == args:
    with user.getRegistry().getLock():
      subuserlib.update.all(user,permissionsAccepter=permissionsAccepter,prompt=options.prompt)
  elif "subusers" == args[0]:
    subusersToUpdate = args[1:]
    if subusersToUpdate:
      with user.getRegistry().getLock():
        subuserlib.update.subusers(user,subusersToUpdate,permissionsAccepter=permissionsAccepter,prompt=options.prompt)
    else:
      sys.exit("You did not specify any subusers to be updated. Use --help for help. Exiting...")
  elif "lock-subuser-to" == args[0]:
    try:
      subuserName = args[1]
      commit = args[2]
    except IndexError:
      sys.exit("Wrong number of arguments.  Expected a subuser name and a commit.  Try running\nsubuser update --help\n for more info.")
    with user.getRegistry().getLock():
      subuserlib.update.lockSubuser(user,subuserName=subuserName,commit=commit)
  elif "unlock-subuser" == args[0]:
    try:
      subuserName = args[1]
    except IndexError:
      sys.exit("Wrong number of arguments.  Expected a subuser's name. Try running\nsubuser update --help\nfor more information.")
    with user.getRegistry().getLock():
      subuserlib.update.unlockSubuser(user,subuserName=subuserName,permissionsAccepter=permissionsAccepter,prompt=options.prompt)
  elif len(args) == 1:
    sys.exit(" ".join(args) + " is not a valid update subcommand. Please use subuser update -h for help.")
  else:
    sys.exit(" ".join(args) + " is not a valid update subcommand. Please use subuser update -h for help.")

if __name__ == "__main__":
  try:
    update(sys.argv[1:])
  except KeyboardInterrupt:
    pass
