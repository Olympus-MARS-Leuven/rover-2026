# rover-2026

all code for the rover from the schoolyear starting in 2026


branch naming convention: [area being changed]/[bug or feature]/[name]
e.g. drive/feature/autonomous-driving



this stuff can be ignored because we are using github desktop

# HOW TO WORK ON THIS REPO:

### Committing:

Committing saves changes on your machine (do this very often)

0. run "git status" to see what has been changed since the previous commit
1. run "git add ." to add all your changes or "git add file_name" to add a specific file ("git restore" can be used to revert changes)
2. run "git commit -m "your message here"" with a message about what you changed
3. if you want to go back to a previous commit you can use "git log --oneline" and "git revert xxxxxxx" with xxxxxxx being the code of the commit you want to revert to

### Pushing:

Once you want to send your changes to the repo, you can push your changes

1. always run "git pull" before pushing changes (skip on the first push of a new branch)
2. run "git push" to send your changes to the repo
3. if you are on a new branch you might get a message about there being no upstream branch, the error should also recommend a command to run that looks something like "git push --set-upstream origin...", just run this command and it should work

### Pulling:

1. run "git pull" to get all the newest code, always do this before working on code
2. you might get a message that you have divergent branches and need to reconcile them, here you can just choose "git config pull.rebase false" and it should be able to figure it out on its own
3. if you get a "merge conflict", you will need to look at the code to see what is conflicting, definitely ask AI for help

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
6. afterwards, run "git checkout main" and "git pull" to get the merged code, and "git branch -d branch_name" to delete your old branch (the branch will be deleted automatically from the repo but it will still exist locally on your computer)

### Merging:

**never merge into main directly, open a pull request instead. this part is just extra knowledge.** \
once you are done with implementing whatever you wanted to implement on a branch, you can use "git merge" to bring those changes to the main branch. in order to do this navigate to the branch you want to merge into (this is normally "main") using "git checkout branch_name". here, run "git pull" to get the newest version. then, merge into that branch using "git merge other_branch_name" (other_branch_name is the branch you are merging into the main branch e.g. "drone/bug/propeller-speed-fix"). this should work without issues, if you get a merge conflict, ask AI. lastly, run "git push" to push everything to the repo.
