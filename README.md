# FamilyCentral
Python Web Application
---

InHouse is a Python/Flask web-application that offers the opportunity to create groups (families) with people and share a shoppinglist, notes section and event list.

## ER and Use-case
![ER Scheme](https://i.postimg.cc/PqFqTHb0/ERWebApp.png)
![Use Case](https://i.postimg.cc/5NcM0yff/UseCase.png)

## Commit History
**2987ecb**6f7743bac1d4926b983c819beab1ecf61
- Initial Commit
- Basic routes like:
	- login
	- logout
	- signup

**3211dbe**1c3f1f31ea5f6c21b8354b6d594710094
- Added login and signup (Vulnerable to SQL injection)

**0e52135**0674616c915b74eae0ba47b0360913257
- Fixed problem that caused crashing on redirect

**a494d06**ea67968768c5320e6a0fd7f896eb8f8ae
- Added decent logging on console

**0456a2c**fd010e0161c5cd858b18c8e5fe39d854d
- Added front end for login and signup routes

**21c3469**c357527f14bfbb565e220a9dd73d86950
- Added back button (small X in top right corner) of login and signup routes

**e58785b**1d34e3ec5878faea12fcbffcbdf9a9575
- Added requirement to fill out forms

**0fc6744**9d922683240f28724d03e41fcaacd1965
- Memorable moment as I found out how to put variables in templates :)

**eee4fe7**4b373d649fdef93db5e697adbd13af127
- Made adminpannel a sub-route of myfamily

**b6bb389**d21c12b244159e3e435016d426d0af40a
- Various changes like redirect instead of error (alreadyInFamily)

**d6e538f**5d901e221296c0f5983efa1d09d51450d
- Added logout button on main menu

**a9cc499**e8cf308265cc3b7b74332691aa635b627
- Memorable moment as this is when the entirety of my database had to be redone to meet standards...

**4403165**e87e95f951d647ee5fa8b983c11198fc1
- Changes in SQL queries to fix verification

**3074f45**349a6572e073062e99dd29dc64c0aa433
- Various changes like instant errors instead of refresh

**2562d50**0024c5500ece08a9c9732ae466c851271
- **Major security patch**
- Added password hashing and prevention for SQL injections 

**aae74a4**16858b0ea0735c80dea4c369ddc04bf9f
- Fixed previous password hashing that actually didn't work

**dd28737**4db6ca5192e45c09076061e7c1303cb3b
- Fixed various bugs that affected redirecting

**2eb9fde**1f6daf5504fe0b15ba9a669469cb0f420
- Finally added README.md with ER Scheme

**f36cc4f**fb30a231ed157afd629824bd6e5d96071
- Added ability to delete entire family

**86d91e9**1072e860386d958f3ba775f0224aaca24
- Added linking and routes to add members to a family

**b33e40b**1a33bee33d11e75d50da7bd4a85d4b0f7
- Added checks to adding members to prevent duplicate families

**4aa7e59**63e64573655237bd03bdcbdaec50fea28
- Fully working invite system with links

**82c108f**65d3252836dd661f6126900edb8bbbc70
- V0.0.1-aplha First complete release
	- Added shoppinglist
	- Added events
