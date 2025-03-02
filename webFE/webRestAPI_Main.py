from flask_restful import Resource, Api

class Items(Resource):
    def get(self):
        return fakeDatabase
class Item(Resource):
    def get(self, pk):
        return fakeDatabase[pk]
