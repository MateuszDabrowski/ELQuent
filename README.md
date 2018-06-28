# ELQuent

Combines multiple utilities automating tasks around Oracle's Eloqua Marketing Automation tool

_Interested in using this tool for your company?
Can help with implementation_

---

## Main modules

### [ELQuent.link](utils/link.py)

#### Clean your links

- RegEx helper
- Quick deletion of Eloqua Tracking from links
- Quick swapping of UTM Tracking Scripts in links
- Allows to update or create e-mail with new code via ELQuent.api module

---

### [ELQuent.mail](utils/mail.py)

#### Constructs your email packages

- RegEx & API builder
- Automatically uploads images and adds image links, tracking scripts and pre-header to package
- Works with both HTML and MJML files
- Outputs HTML, MJML, updates e-mail or creates new one directly in Eloqua
- Uses PURL to ensure field merges on linked sites will be working

---

### [ELQuent.page](utils/page.py)

#### Create landing page

- RegEx work automator
- Allows user to automatically swap Eloqua Form in Landing Page
- Allows to use built-in landing page templates for quick deployment
- Cleans code, appends snippets, changes form code

_ToDo:_

- [ ] _Change from two (one and two column) LP templates to just one modular template_
- [ ] _Add optional questions for template filling as in campaign flow_

---

### [ELQuent.campaign](utils/campaign.py)

#### Builds Eloqua Campaigns

- Built-in wizard creating all Landing Pages required for campaign
- Creates blindform for confirmation-ty-lp and automatically impelements it
- Creates confirmation (plus reminder) e-mail and fills it with gathered data
- Creates asset name with link to the chosen asset
- Updates confirmation form with asset e-mail and asset link
- Creates campaign canvas filled with created content
- Basic campaign canvas flow for mail+reminder sends
- Simple Email Campaign without canvas flow

_ToDo:_

- [ ] _Randomized subject & pre-header generator for technical e-mail_
- [ ] _Update main form with confirmation e-mail ID and thank-you-page urls_
- [ ] _When not recognized product name, try to find best matches from a list_

---

### [ELQuent.webinar](utils/webinar.py)

#### Add viewers to Eloqua

- ClickMeeting API connector app
- Allows user specify time range for webinar data import
- Automatically gets all needed data via API and restructures it
- Uploads contacts to Eloqua shared list via ELQuent.api module

---

### [ELQuent.database](utils/database.py)

#### Create Eloqua-compliant contact upload file

- Gets input from user
- Allows appending, trimming and intersecting e-mail uploads
- Outputs .csv file with correct structure and naming convention
- Uploads contacts to Eloqua shared list via ELQuent.api module
- Cleans data import dependency after succesful upload

---

### [ELQuent.export](utils/export.py)

#### Module focused on exporting data from Eloqua instance

- Gets full bounceback activity data from chosen timeframe
- Saves bounceback export data to .json and .csv files

---

### [ELQuent.corp](utils/corp.py)

#### Specialized utils for core admins

- Creates forms and shared lists for e-mail group control based on country splitted json file
- Creates program canvas and automatically adds above assets to program steps

---

## Helper modules

### [ELQuent.api](utils/api/api.py)

#### Helper module for Eloqua API

- Authenticates user
- Uploads contact database to Eloqua shared lists
- Cleans import definition after successful upload to clean dependecies
- Checks if LP, Form, Mail already exists on Eloqua instance
- Uploads landing page to specified folder
- Gets all necessary data to upload an e-mail
- Uploads e-mail to json specified folder
- Updates e-mail with new code
- Adds Eloqua tracking to e-mail links
- Uploads form to json specified folder
- Updates form with html, css and processing steps
- Gets form fields and form fills data
- Creates campaign and program canvas
- Creates shared filters
- Creates export definition for activity API and downloads data from it
- Refreshes and download segment counts

---

### [ELQuent.helper](utils/helper.py)

#### Helper module for Eloqua conventions

- Gets valid campaign name from user (according to predefined naming convention)
- Gets type of campaign from user
- Gets converting asset name for the campaign
- Gets link to the asset
- Gets promoted product name either from campaign name (via naming convention) or from user
- Gets optional header text

---

Copyright (c) 2018 Mateusz Dąbrowski [MIT License](LICENSE)

[_Version: 1.7.11_]