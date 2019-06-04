#!/usr/bin/python

import os
import requests
from lxml import html
from time import sleep
import mysql.connector
from datetime import datetime
from selenium import webdriver
from fuc_agent import get_agent


# from requests.packages.urllib3.exceptions import InsecureRequestWarning

# 禁用安全请求警告
# requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

#   Function to get evidence image base on provided link
def get_image(url):
    name = str((url.split('/')[-1]).replace('-', '_'))
    print('Launching Firefox..')
    # date = (datetime.datetime.now().date())
    browser = webdriver.Firefox()
    browser.get(url)
    # screenshot = browser.save_screenshot("%s(%s).png" % (name, date))
    screenshot_png = browser.get_screenshot_as_png()
    print('Closing Firefox..')
    browser.close()
    return screenshot_png


#   Function to check& update existing record from DB
def check_db(link_id):
    try:
        connection = mysql.connector.connect(host='localhost',
                                             port='8889',
                                             database='price_db',
                                             user='root',
                                             password='root')
        sql_select_query = """ SELECT last_update FROM `product_cat` WHERE link_id = %s"""
        cursor = connection.cursor()
        #   cursor.execute(sql_insert_query, (link_id,))  standard format:  (variable,)     !!!!!
        cursor.execute(sql_select_query, (link_id,))
        records = cursor.fetchall()
        if records:
            print("Found Record")
            for row in records:
                if row[0] > (datetime.now().date()):
                    print("Impossible")
                elif row[0] < (datetime.now().date()):
                    print("Outdated")
                    #   insert data to 1 db
                    #   pull the history data
                else:
                    print("Current")
                    #   pull the history data
        else:
            print("No Record!")

            #   insert data to 2 database

    except mysql.connector.Error as error:
        connection.rollback()  # rollback if any exception occured
        print("Failed inserting record into price_db table. {}".format(error))

    finally:
        # closing database connection.
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("MySQL connection is closed")


#   Function for insert into database
# def insert_db(p_id, p_vendor, p_name, p_price, p_img, time, l_id):

def insert_db(p_id, p_vendor, p_name, p_price, time, l_id, update, create):
    # print(kwargs)
    #   Create New Record
    if not update and create:
        try:
            connection = mysql.connector.connect(host='localhost',
                                                 port='8889',
                                                 database='price_db',
                                                 user='root',
                                                 password='root')
            sql_insert_query = """ INSERT INTO `product_history`(`product_id`, `vendor`, `name`, `price`, `date`) VALUES (%s,%s,%s,%s,%s)"""
            sql_insert_query2 = """ INSERT INTO `product_cat`(`product_id`, `vendor`, `name`, `last_update`, `link`, `link_id`) VALUES (%s,%s,%s,%s,%s,%s)"""
            cursor = connection.cursor()
            p_info = (p_id, p_vendor, p_name, p_price, time)
            p_link = 'https://www.chemistwarehouse.com.au/buy/%s' % l_id
            c_info = (p_id, p_vendor, p_name, time, p_link, l_id)
            cursor.execute(sql_insert_query, p_info)
            cursor.execute(sql_insert_query2, c_info)
            connection.commit()
            print("Record inserted successfully into Database")
        except mysql.connector.Error as error:
            connection.rollback()  # rollback if any exception occured
            print("Failed inserting record into database. {}".format(error))

        finally:
            # closing database connection.
            if (connection.is_connected()):
                cursor.close()
                connection.close()

    #   Update Existing Record
    elif update and not create:
        print("update existing one")
        try:
            connection = mysql.connector.connect(host='localhost',
                                                 port='8889',
                                                 database='price_db',
                                                 user='root',
                                                 password='root')
            sql_insert_query = """ INSERT INTO `product_history`(`product_id`, `vendor`, `name`, `price`, `date`) VALUES (%s,%s,%s,%s,%s)"""
            sql_insert_query2 = """ UPDATE `product_cat` SET last_update = %s WHERE link_id = %s """
            cursor = connection.cursor()
            p_info = (p_id, p_vendor, p_name, p_price, time)
            c_info = (time, l_id)
            cursor.execute(sql_insert_query, p_info)
            cursor.execute(sql_insert_query2, c_info)
            connection.commit()
            print("Record update successfully")
        except mysql.connector.Error as error:
            connection.rollback()  # rollback if any exception occured
            print("Failed update record. {}".format(error))

        finally:
            # closing database connection.
            if (connection.is_connected()):
                cursor.close()
                connection.close()
    elif not update and not create:
        print("record up to date")
    else:
        print("Impossible")


#   Main function to extract data , image and insert into database
def get_data(url):
    response = requests.get(url, timeout=2, headers={'User-Agent': get_agent()}).text
    selector = html.fromstring(response)

    # -----This is for different vendor-----
    if "chemistwarehouse" in url:
        product_vendor = 'ChemistWarehouse'
    elif "mychemist" in url:
        product_vendor = 'MyChemist'
    else:
        product_vendor = 'Unknow'

    #   Link page validation
    if (len(selector.xpath('//*[@class="productDetail"]'))) == 0:
        return
    else:
        product_id = ((selector.xpath('//*[@class="product-id"]/text()')[0]).split(':')[-1]).strip()
        product_name = (selector.xpath('//*[@class="product-name"]/h1/text()')[0]).strip()
        product_price = (selector.xpath('//*[@class="Price"]/span/text()')[0]).split("$")[-1]
        capture_time = datetime.now().date().strftime('%Y-%m-%d')

        #   Check database for product info
        link_id = link.split('/')[-1]

        #   Condition check for next step
        try:
            connection = mysql.connector.connect(host='localhost',
                                                 port='8889',
                                                 database='price_db',
                                                 user='root',
                                                 password='root')
            sql_select_query = """ SELECT last_update FROM `product_cat` WHERE link_id = %s"""
            cursor = connection.cursor()
            #   cursor.execute(sql_insert_query, (link_id,))  standard format:  (variable,)     !!!!!
            cursor.execute(sql_select_query, (link_id,))
            records = cursor.fetchall()
            if records:
                print("Found Record")
                for row in records:
                    if row[0] > (datetime.now().date()):
                        print("Impossible")
                    elif row[0] < (datetime.now().date()):
                        print("Outdated")
                        insert_db(p_id=product_id, p_vendor=product_vendor, p_name=product_name, p_price=product_price,
                                  time=capture_time, l_id=link_id, update=True, create=False)
                        #   pull the history data
                    else:
                        print("Current")
                        insert_db(p_id=product_id, p_vendor=product_vendor, p_name=product_name, p_price=product_price,
                                  time=capture_time, l_id=link_id, update=False, create=False)
                        #   pull the history data
            else:
                print("No Current Record!")
                # Insert Into Databse
                insert_db(p_id=product_id, p_vendor=product_vendor, p_name=product_name, p_price=product_price,
                          time=capture_time, l_id=link_id, update=False, create=True)

        except mysql.connector.Error as error:
            connection.rollback()  # rollback if any exception occured
            print("Failed inserting record into price_db table. {}".format(error))

        finally:
            # closing database connection.
            if connection.is_connected():
                cursor.close()
                connection.close()
                print("MySQL connection is closed")

            # -----This is for evidence image(Options)-----
            # product_img = get_image(url)

            # Insert Into Databse

    return True


if __name__ == '__main__':
    # link = 'https://www.chemistwarehouse.com.au/buy/65966'
    link = 'https://www.chemistwarehouse.com.au/buy/65961'
    # link = 'https://www.chemistwarehouse.com.au/buy/65962'
    if get_data(link) is None:
        print("Product not found")
    else:
        print("Product found")
