import copy
from collections import defaultdict

#can be run by python3.7 -m cart

class Category:

    def __init__(self, name,parent = None):
        self.name = name
        self.parent=parent

    def detail(self):
        return "name {} parent {} ".format(self.name, self.parent)


class Product:

    def __init__(self, title,price,category):
        self.title = title
        self.price = price
        self.discount_price = price
        self.coupon_price = price
        self.category=category

    def description(self):
        return "title {} price {} category {} ".format(self.title, self.price,self.category.detail())


class Campaign:

    def __init__(self, category,value,count,type):
        self.category = category
        self.value = value
        self.count=count
        self.type=type


class Coupon:

    def __init__(self, min_value,count,type):
        self.min_value = min_value
        self.count=count
        self.type=type


class Cart:

    def __init__(self):
        self.items = []
        self.purchase=0
        self.purchase_campaign=0
        self.purchase_reduced=0
        self.categories = defaultdict(list)
        self.products = set([])
        self.total_amount=0

    def addItem(self,product,amount):
        #this method is to add item to a cart and specify related fields in cart
        item={
            "product":copy.copy(product),
            "amount":amount,
        }
        self.items.append(item)
        self.categories[product.category.name].append(item)
        self.add_to_parent(product.category,item)
        self.total_amount+=amount
        self.products.add(product)
        self.purchase+=amount*product.price
        self.purchase_campaign+=amount*product.price
        self.purchase_reduced += amount * product.price
        return self.items

    def add_to_parent(self,category,item):
        #this method is to add child's items to parent as well because any item in child is also in parent
        if category.parent is not None:
            self.categories[category.parent.name].append(item)
            self.add_to_parent(category.parent,item)


    def applyOneDiscount(self, campaign):
        #this method is an intermediate method which applies given campaign
        category = campaign.category
        list_category=self.categories[category.name]
        amount=0
        for item in list_category:
            amount+=item['amount']
        if amount>campaign.count:
            if campaign.type is 'rate':
                value=0
                for item in list_category:
                    value+=item['product'].discount_price*item['amount']
                    item['product'].discount_price = item['product'].discount_price * (100 - campaign.value) / 100
                self.purchase_campaign = self.purchase_campaign - value * (campaign.value) / 100
            else :
                if campaign.type is 'amount':
                    sub_value=0
                    for item in list_category:
                        if item['product'].discount_price - campaign.value > 0:
                            item['product'].discount_price = item['product'].discount_price - campaign.value
                            sub_value +=campaign.value*item['amount']
                        else:
                            sub_value+=item['product'].discount_price*item['amount']
                            item['product'].discount_price=0
                    self.purchase_campaign = self.purchase_campaign - sub_value


    def applyDiscount(self,campaign_list):
        #this method is one of the apply discount methods this applies campagns directly
        for campaign in campaign_list:
            self.applyOneDiscount(campaign)

    def applyMaximizeDiscount(self,campaign_list):
        #this method is to reorder discount list to maximize affect of discounts
        #it runs every rate type discounts then amount type because if it runs amount first it decreases effect of rate
        campaign_amount_list=[]
        for campaign in campaign_list:
            if campaign.type == 'amount':
                campaign_amount_list.append(campaign)
            else:
                self.applyOneDiscount(campaign)
        for campaign in campaign_amount_list:
            self.applyOneDiscount(campaign)

    def applyBestOfDiscounts(self,campaign_list):
        #this method finds most effective discount and runs it
        max_discount=0
        index_max_discount=0
        index_counter=0
        for campaign in campaign_list:
            category=campaign.category
            count=0
            value=0
            index=[]
            item_count=0
            for item in self.items:
                if item['product'].category==category:
                    count+=item['amount']
                    value+=item['amount']*item['product'].discount_price
                    index.append(item_count)
                item_count+=1
            if count > campaign.count:
                if campaign.type is 'rate':
                    if max_discount<value*(campaign.value)/100:
                        max_discount=value*(campaign.value)/100
                        index_max_discount=index_counter
                else:
                    if campaign.type is 'amount':
                        product_amount=0
                        for item in self.categories[campaign.category.name]:
                            product_amount+=item['amount']
                        if max_discount < campaign.value*product_amount:
                            max_discount = campaign.value*product_amount
                            index_max_discount = index_counter
            index_counter+=1
        self.applyOneDiscount(campaign_list[index_max_discount])


    def applyCoupon(self,coupon):
        #this method apples discounts
        if self.purchase_campaign > coupon.min_value:
            if coupon.type is 'rate':
                self.purchase_reduced=self.purchase_campaign*(100-coupon.count)/100
                for item in self.items:
                    item['product'].coupon_price=item['product'].discount_price*(100-coupon.count)/100
            else :
                if coupon.type is 'amount':
                    sub_value=0
                    for item in self.items:
                        if item['product'].discount_price -(coupon.count/self.total_amount) > 0:
                            sub_value+=(coupon.count*item['amount']/self.total_amount)
                            item['product'].coupon_price = item['product'].discount_price -(coupon.count/self.total_amount)
                        else:
                            sub_value+=item['product'].discount_price*item['amount']
                            item['product'].coupon_price=0
                    self.purchase_reduced=self.purchase_campaign-sub_value
        else:
            self.purchase_reduced = self.purchase_campaign
            for item in self.items:
                item['product'].coupon_price = item['product'].discount_price



    def getTotalAmountAfterDiscounts(self):
        return self.purchase_reduced


    def getCouponDiscount(self):
        return self.purchase_campaign-self.purchase_reduced

    def getCampaignDiscount(self):
        return self.purchase-self.purchase_campaign

    def getDeliveryCost(self):
        calculator = DeliveryCostCalculator(3, 2.5, 3)
        return calculator.calculateFor(self)

    def calculate_discount(self,item):
        return (item['product'].price-item['product'].coupon_price)*item['amount']


    def print(self):
        for category in self.categories:
            temp=self.categories[category]
            for entry in temp:
                print("category name {} product name {} quantity {} unit price {} total price {} total discount {} ".format(category, entry["product"].title,entry["amount"],entry["product"].price,(entry["product"].price*entry["amount"]), self.calculate_discount(entry)))

class DeliveryCostCalculator:

    def __init__(self, costPerDelivery,costPerProduct,fixedCost):
        self.costPerDelivery = costPerDelivery
        self.costPerProduct = costPerProduct
        self.fixedCost=fixedCost

    def calculateFor(self,cart):
        number_of_deliveries=len(cart.categories)
        number_of_products=len(cart.products)
        return (self.costPerDelivery*number_of_deliveries)+(self.costPerProduct*number_of_products)+self.fixedCost

#There ate three main test part to evaluate every aspect
#In first part first I create two categories and three product in that categories
#grocery category is parent of fruit category so any campaign in grocery will also affect fruit category
print("TEST 1")
category=Category("grocery")
new_category=Category("fruit",category)
product_egg=Product("eggplant",100,category)
product_pumb=Product("pumpkin",100,category)
product_apple=Product("apple",90,new_category)
#creating new cart and adding product to that cart
cart=Cart()
temp=cart.addItem(product_egg,3)
temp2=cart.addItem(product_pumb,3)
temp3=cart.addItem(product_apple,3)
#creating 4 campaigns and campaign 4 will not affect because in fruit category total amount is 3 but required amount in campaign4 is 5
campaign=Campaign(category,10,3,'rate')
campaign2=Campaign(category,50,3,'amount')
campaign3=Campaign(new_category,15,2,'amount')
campaign4=Campaign(new_category,15,5,'amount')
campain_list=[campaign,campaign2,campaign3,campaign4]
#coupon reduce 10 percent of every item in cart
coupon=Coupon(100,10,'rate')
#applyMaximizeDiscount apply all discounts with maximizing order
cart.applyMaximizeDiscount(campain_list)
cart.applyCoupon(coupon)
#we are expecting 192 total discount in eqqplant and pumpkin because first capmaign1 reduce 10 percent which reduce 10 for every item
#then reduce 50 every element in that items because of campaign2
#campaign3 does not affect grocery category
#then coupon reduce 10 percent in total for every unit there is 10+50+(40*0.1) reduce which is 64 for every unit and for 3 unit 192
#for apple first 10 percent reduce 50 amount reduce 15 amount reduce and then 10 percent reduce
#this means that for every apple unit 9+50+15+16*0.1=75.6 for 3 apple 226.8
cart.print()
#Expected delivery cost is 16.5 because number of deliveries in this cart is 2 number of different products is 3
#I identify cost per delivery as 3 cost per product as 2.5 and 3 fixed cost
#in total 2*3+2.5*3+3
print("Delivery cost "+str(cart.getDeliveryCost()))
print("Total amount after discounts "+ str(cart.getTotalAmountAfterDiscounts()))
print("Discount from coupon "+ str(cart.getCouponDiscount()))
print("Discount from campaign "+ str(cart.getCampaignDiscount()))

#In second part there are 3 categories and 4 products
#technology is parent of earpod and grocery is irrelevant to them
print("TEST 2")
category_tech=Category("technology")
new_category=Category("earpod",category_tech)
product_tv=Product("tv",1500,category_tech)
product_note=Product("notebook",1200,category_tech)
product_apple_earpod=Product("apple_earpod",900,new_category)
product_pumb=Product("pumpkin",100,category)
new_cart=Cart()
temp_tech=new_cart.addItem(product_tv,2)
temp2_tech=new_cart.addItem(product_note,4)
temp3_tech=new_cart.addItem(product_apple_earpod,3)
new_cart.addItem(product_pumb,3)
campaign_tech=Campaign(category_tech,10,3,'rate')
campaign2_tech=Campaign(category_tech,1300,4,'amount')
campaign3_tech=Campaign(new_category,15,2,'amount')
campain_list=[campaign_tech,campaign2_tech,campaign3_tech]
coupon=Coupon(1000,10,'rate')
#for this case I use applyBestOfDiscounts this chooses the campaign which reduces according to that campaign
#the most effective campain is campaign2_tech
new_cart.applyBestOfDiscounts(campain_list)
#after applying discounts remaining payment is 700 so coupon should not be applied
new_cart.applyCoupon(coupon)
#for tv product there is only 1300 amount of discount initial price was 1500 so discount should be 2600 for that
#for notebook initial price is 1200 so 1300 units reducement should only affect 1200 because price could not be below zero
#because earpods are also in technology category 1300 units reducement should also affect product_apple_earpod
#price of earpod is 900 which is lower that reducement so it should also decrease to 0
#product_pumb will not be affected because there is not any campaign for grocery and coupon could not be used because total amount reduced below 1000
new_cart.print()
#Expected delivery cost is 22 because number of deliveries in this cart is 3 number of different products is 4
#I identify cost per delivery as 3 cost per product as 2.5 and 3 fixed cost
#in total 3*3+2.5*4+3
print("Delivery cost "+str(new_cart.getDeliveryCost()))
print("Total amount after discounts "+ str(new_cart.getTotalAmountAfterDiscounts()))
print("Discount from coupon "+ str(new_cart.getCouponDiscount()))
print("Discount from campaign "+ str(new_cart.getCampaignDiscount()))

#In third part there are 2 categories and 3 products
#furniture is parent of kitchen
print("TEST 3")
category_furniture=Category("furniture")
new_category=Category("kitchen",category_furniture)
product_chair=Product("chair",500,category_furniture)
product_couch=Product("couch",1200,category_furniture)
product_blender=Product("blender",90,new_category)
new_furniture_cart=Cart()
new_furniture_cart.addItem(product_chair,2)
new_furniture_cart.addItem(product_couch,4)
new_furniture_cart.addItem(product_blender,3)
campaign_furniture=Campaign(category_furniture,25,3,'rate')
campaign2_furniture=Campaign(category_furniture,13,4,'amount')
campaign3_furniture=Campaign(new_category,15,2,'amount')
campain_list=[campaign_furniture,campaign2_furniture,campaign3_furniture]
coupon=Coupon(1000,900,'amount')
#for this case I use applyBestOfDiscounts this chooses the campaign which reduces according to that campaign
#the most effective campain is campaign_furniture
new_furniture_cart.applyBestOfDiscounts(campain_list)
#coupon value is 900 and type is amount and in total there are 2 chair 4 couch and 3 blender so for every unit it tries to reduce 100
#because after applying campaign_furniture blender reduces 67.5(25 percent reducement campaign) it reduces 67.5 in price of blender
new_furniture_cart.applyCoupon(coupon)
#for chair we expect 225 unit of reducement for every element of this product and 450 in tottal because price is 500 and first 25 percent reducement which leads 125 discount
#then 100 reducement when applied coupon
#for furniture initial price is 1200 25 percent reducement 300 then 100 reducement from coupon so 400 for every unit in total 4*400 1600 reducement
#for blender first 25 percent reducement 90 to 67.5 then coupon only reduce 67.5 units so for every unit 90 discount for all 270 discount
new_furniture_cart.print()
#Expected delivery cost is 16.5 because number of deliveries in this cart is 2 number of different products is 3
#I identify cost per delivery as 3 cost per product as 2.5 and 3 fixed cost
#in total 2*3+2.5*3+3
print("Delivery cost "+str(new_furniture_cart.getDeliveryCost()))
print("Total amount after discounts "+ str(new_furniture_cart.getTotalAmountAfterDiscounts()))
print("Discount from coupon "+ str(new_furniture_cart.getCouponDiscount()))
print("Discount from campaign "+ str(new_furniture_cart.getCampaignDiscount()))
