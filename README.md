# rover-2026
all code for the rover from the schoolyear starting in 2026




# HOW TO WORK ON THIS REPO:

## Initial Cloning:
### Part 1: set up a ssh key and connect it to your github account
If you run "ls ~/.ssh" and see id_ed25519 and id_ed25519.pub, you can skip to step 4 (or if you have already added a key to github skip this part entirely)
#### Steps:
1. open terminal on Mac/Linux or Git Bash on Windows (you might have to install it, just search “git download windows”)
2. run this command (with your email): ssh-keygen -t ed25519 -C "your-email@example.com"
3. just press enter three times for an empty passphrase
4. run this on Mac: pbcopy < ~/.ssh/id_ed25519.pub\
   or this on Windows: clip < ~/.ssh/id_ed25519.pub\
   or this on Linux (and then copy the full printed key): cat ~/.ssh/id_ed25519.pub
5. go to github.com -> settings -> SSH and GPG keys -> New SSH key -> paste the key in "key" box and give it whatever name you want -> click Add SSH Key
6. run this command: ssh -T git@github.com\
   it should return "Hi <username>! You've successfully authenticated, but GitHub does not provide shell access."\
   (you might get a prompt to type "yes" first)
8. run these two commands with Your Name and your-email@example.com replaced:\
    git config --global user.name "Your Name"\
    git config --global user.email "your-email@example.com"

### Part 2: clone the repo
#### Steps:
0. accept the invitation to the Olympus-MARS-Leuven organization (check your email)
1. use Terminal/Git Bash to navigate to the folder in which you want to place the repo\
   you can use the "cd path/to/folder" command for this
2. go to https://github.com/Olympus-MARS-Leuven/rover-2026 and click on the green "Code" button
3. go to SSH and copy the SSH link
4. run "git clone [SSH link]"
5. Done!!!

## Making Changes:
### Committing:
Committing saves changes on your machine (do this very often)
1. run "git add ." to add all your changes
2. run "git commit -m "your message here"" with a message about what you changed

### Pushing:
Once you want to send your changes to the repo, you can push your changes
1. always run "git pull" before pushing changes (skip on the first push of a new branch)
2. run "git push" to send your changes to the repo
3. if you are on a new branch you might get a message about there being no upstream branch, the error should also recommend a command to run that looks something like "git push --set-upstream origin...", just run this command and it should work

### Pulling:
1. run "git pull" to get all the newest code, always do this before working on code
2. if you get a "merge conflict", you will need to look at the code to see what is conflicting, definitely ask AI for help

### Branches:
different branches should be used when implementing different features so that the code doesn't get messed up because multiple people are working on it at the same time. switching between branches is done using the "git checkout branch_name" command. changes you have committed do not come with you when switching branches, uncommitted changes do (try) to come with you, so always remember to commit your changes before switching branches.

in order to create a new branch you can use "git checkout -b branch_name". in order to keep everything organized it is best to make use of a naming convention. we will use "[area being changed]/[bug or feature]/[name], e.g. if you are fixing a bug with the propeller speed of the drone, you might do "git checkout -b drone/bug/propeller-speed-fix". or when adding a new autonomous driving feature to the drive, you might do "git checkout -b drive/feature/autonomous-driving".

### Pull Requests:
once you are done with implementing whatever you wanted to implement on a branch, you can make a pull request to merge your changes onto the main branch. this is done using a pull request so that someone can check your work before pushing to main.
1. commit and push your changes as usual (see above)
2. go to https://github.com/Olympus-MARS-Leuven/rover-2026 and click "Compare & pull request" on the yellow banner\
   (or go to Pull requests -> New pull request and select your branch)
3. write a short description of what you changed, add a reviewer on the right and click "Create pull request"
4. if the reviewer asks for changes, just commit and push to the same branch, the pull request updates automatically
5. once it's approved, click "Merge pull request"
6. afterwards, run "git checkout main" and "git pull" to get the merged code, and "git branch -d branch_name" to delete your old branch

### Merging:
**never merge into main directly, open a pull request instead. this part is just extra knowledge.** \
once you are done with implementing whatever you wanted to implement on a branch, you can use "git merge" to bring those changes to the main branch. in order to do this navigate to the branch you want to merge into (this is normally "main") using "git checkout branch_name". here, run "git pull" to get the newest version. then, merge into that branch using "git merge other_branch_name" (other_branch_name is the branch you are merging into the main branch e.g. "drone/bug/propeller-speed-fix"). this should work without issues, if you get a merge conflict, ask AI. lastly, run "git push" to push everything to the repo.





Using VS Code instead of the terminal:

everything above can also be done with buttons in VS Code's built in git manager. the rules stay the same (pull before working, use branches with the naming convention, never merge into main directly), only how you do it changes. you still need to do Part 1 (ssh key + git config) first.
the git manager is the "Source Control" tab on the left sidebar (the icon that looks like a branch), or press Ctrl+Shift+G (Cmd+Shift+G on Mac).

Cloning:

    accept the invitation to the Olympus-MARS-Leuven organization (check your email)
    copy the SSH link the same way as in Part 2
    in VS Code, press Ctrl+Shift+P (Cmd+Shift+P on Mac), type "Git: Clone" and press enter
    paste the SSH link and press enter
    choose the folder in which you want to place the repo
    click "Open" when VS Code asks if you want to open the cloned repo

Committing:

    open the Source Control tab, all the files you changed are listed under "Changes"
    click the "+" next to "Changes" to stage all files (this is the same as "git add ."), or the "+" next to a single file to only stage that one
    type a message about what you changed in the message box at the top
    click "Commit"
    (if you click "Commit" without staging anything, VS Code asks if it should stage all your changes and commit them, you can just click "Yes")

Pulling:

    in the Source Control tab, click the "..." at the top -> Pull
    always do this before working on code

Pushing:

    always pull first (see above)
    after committing, click "..." -> Push
    or just click the "Sync Changes" button that shows up after committing, this pulls and then pushes in one go
    on a new branch the button says "Publish Branch" instead, just click it (this replaces the "git push --set-upstream origin..." command)

Merge conflicts:

    conflicting files show up under "Merge Changes" in the Source Control tab
    open the file, above every conflict you can click "Accept Current Change", "Accept Incoming Change" or "Accept Both Changes" (definitely ask AI for help if you're not sure which one)
    once every conflict in a file is fixed, stage it with "+" and commit like normal

Branches:

    the name of your current branch is shown in the bottom left corner of VS Code
    click it to get a list of all branches, pick one to switch to it (this is the same as "git checkout branch_name")
    to create a new branch, click it and choose "+ Create new branch...", then type the name using the naming convention (e.g. drone/bug/propeller-speed-fix)
    the new branch starts from the branch you are currently on, so switch to main and pull first
    same as before: commit your changes before switching branches

Pull Requests:

    commit and push/publish your branch as usual (see above)
    then make the pull request on the github website, exactly like in the Pull Requests section above
    afterwards, switch to main using the branch name in the bottom left, pull, and delete your old branch with "..." -> Branch -> Delete Branch...

Merging:

    same rule: never merge into main directly, open a pull request instead
    for extra knowledge: switch to the branch you want to merge into, pull, then click "..." -> Branch -> Merge..., pick the other branch, then push
