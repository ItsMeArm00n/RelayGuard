# Upload this source to GitHub

1. Extract **RelayGuard-GitHub.zip** into an empty folder.
2. Open that folder. README.md, app.py, static/, docs/, and the other source files should be directly inside it.
3. Create an empty GitHub repository, for example `relayguard`. You do not need GitHub to generate another README.
4. Choose **Add file → Upload files** and upload the extracted contents, including folders. Upload source files, not the ZIP itself. Make sure README.md is at the repository root so GitHub displays it automatically.
5. Include the hidden `.gitignore` and `.gitattributes` files. Windows File Explorer's **View → Show → Hidden items** can reveal them if needed.
6. Commit the upload. Open the repository's main page to check the banner, table of contents, architecture diagram, and documentation links.

Do not add archive.zip, runtime/, your local environment, private keys, or exported bank-review records. The source archive excludes them and provides ignore rules.

GitHub stores this project's source. GitHub Pages alone cannot execute the Python backend or AI model. Use the local instructions or LinuxONE deployment guide to run the application.

For the hackathon, include your team name in the submission title and share the repository URL alongside the demo video. Review team attribution and choose a project-source license if you want to grant explicit reuse rights; this package does not choose one on your behalf.
