#Input prompt to generate hashed passwords

import hashlib

hash = hashlib.sha256()
clearInput = input('> ')
hash.update(clearInput.encode('utf-8'))
hashed = hash.hexdigest()

print(hashed)