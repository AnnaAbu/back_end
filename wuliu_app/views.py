# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from .utils import *
from .verify import gene_code
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.sessions.backends.db import SessionStore
from django.contrib.sessions.models import Session
from . import conf
import os


def __op_add(src_dict, files):
    sql_add = get_insert_sql(eval(src_dict['data']))
    result_row = sql_execute(sql_add, True)
    return 'add_successfully' + str(result_row)


def __op_delete(src_dict, files):
    sql_delete = get_delete_sql(src_dict['id'])
    result_row = sql_execute(sql_delete, True)
    return 'delete_successfully' + str(result_row)


def __op_update(src_dict, files):
    sql_update = get_update_sql(src_dict['id'], eval(src_dict['data']))
    result_row = sql_execute(sql_update, True)
    return 'add_successfully' + str(result_row)


def __op_select(src_dict, des_list, filter_list):
    categories = []
    show_num = src_dict.get('num', '1')
    if 'category' in filter_list:
        filter_list.remove('category')
        categories = src_dict.getlist('category[]', [conf.CONF_NULL])
        for category in categories:
            if category not in conf.VALID_CATEGORIES:
                raise Exception('invalid category')
    filter_dict = {}
    for item in filter_list:
        filter_dict[item] = src_dict[item]
    sql_select = get_select_sql(des_list, show_num, filter_dict, categories, table='article')
    result_tuple = sql_execute(sql_select)
    dict_list = []
    for row in result_tuple:
        temp_dict = {}
        for i in range(len(row)):
            temp_dict[des_list[i]] = row[i]
        dict_list.append(temp_dict)
    return dict_list


def __lay_list(src_dict, des_list):
    categories = src_dict.getlist('category[]', ['all'])
    page = src_dict.get('page', 0)
    num = src_dict.get('num', 3)
    average = src_dict.get('average', conf.CONF_FALSE)
    start = int(page) * int(num)
    desc_str = ','.join(des_list)
    if 'all' in categories:
        part = src_dict.get('part', conf.CONF_NULL)
        if part == conf.CONF_NULL:
            raise Exception('invalid part in lay_list')
        sql = 'select ' + desc_str + ' from article where part="' + part + '" limit ' + str(start) + ', ' + str(num)
    else:
        sql_category = ''
        for category in categories:
            if category not in conf.VALID_CATEGORIES:
                raise Exception('invalid category')
            sql_category += 'category ="' + category + '" or '
            sql_category = sql_category[:-3]
        if average == conf.CONF_TRUE:
            sql = " select " + desc_str + " from article as a where (select count(*) from" + \
                  " article as b where b.category=a.category and b.id>=a.id)<= " + str(
                num) + " and( " + sql_category + ")"
        else:
            sql = "select " + desc_str + " from article where " + sql_category + " limit " \
                  + str(start) + ', ' + num
    ct = sql_execute(sql)
    data = []
    for c in ct:
        temp_dict = {}
        for i in range(len(c)):
            temp_dict[des_list[i]] = c[i]
        data.append(temp_dict)
    return data


def index(request):
    if request.method == 'GET':
        return JsonResponse({'status': 1, 'data': {'error': 'only post allow'}})
    elif request.method == 'POST':
        branch = request.POST.get('branch', 'null')
        try:
            #import ipdb;ipdb.set_trace()
            if branch == 'op_add':
                data = __op_add(request.POST, request.FILES)
            elif branch == 'op_delete':
                data = __op_delete(request.POST, request.FILES)
            elif branch == 'op_update':
                data = __op_update(request.POST, request.FILES)
            elif branch == 'lay_content':
                # import ipdb;ipdb.set_trace()
                data = __op_select(request.POST, ['id', 'content', 'part', 'category'], ['part', 'category'])
            elif branch == 'lay_details':
                # import ipdb;ipdb.set_trace()
                data = __op_select(request.POST, ['id', 'title', 'content', 'timestamp', 'part', 'category'],
                                   ['id'])
            elif branch == 'lay_list':
                import ipdb;ipdb.set_trace()
                data = __lay_list(request.POST, ['id', 'title', 'timestamp', 'part', 'category'])
            elif branch == 'lay_news':
                data = __op_select(request.POST, ['id', 'title', 'content', 'image_url', 'part', 'category'],
                                   ['part', 'category'])
            elif branch == 'lay_carousel':
                data = __op_select(request.POST, ['id', 'image_url', 'part', 'category'], ['part', 'category'])
            else:
                data = {'message': 'invalid branch'}
            status = 0
        except Exception as e:
            status = 2
            data = {'error': e}
        return JsonResponse({'status': status, 'data': data})
    else:
        return JsonResponse({'status': 3, 'data': {'error': 'invalid post'}})


def __save_session(**kwargs):
    sessionStore = SessionStore()
    # if 'iden_code' in kwargs:
    #     sessionStore['iden_code'] = kwargs['iden_code']
    # if 'user_name' in kwargs:
    #     sessionStore['user_name'] = kwargs['user_name']
    for key in kwargs.keys():
        sessionStore[key] = kwargs[key]
    sessionStore.save()
    session_key = sessionStore.session_key
    return session_key


def __read_session(session_key):
    session = Session.objects.get(pk=session_key)
    #print(session.session_data)  # 返回session的存储（加密过）
    return session.get_decoded()  # 返回session的数据结构（加过解码）
    #print(session.expire_date)


def login_page(request):
    try:
        temp_dict = {}
        temp_dict = gene_code()
        session_key = __save_session(iden_code = temp_dict['text'],pic_url = temp_dict['pic_url'])
        data = {}
        data['pic_url'] = temp_dict['pic_url']
        data['session_key'] = session_key
        return JsonResponse({'status': 0, 'data': data})
    finally:
        os.remove(session['pic_url'])

def login1(requset):
    if requset.method == 'POST':
        #import ipdb; ipdb.set_trace()
        try:
            session_key = requset.POST.get('session_key')
            session = __read_session(session_key)
            data = {}
            #注意验证码区分大小写
            if requset.POST['iden_code'] != session['iden_code']:
                status = 4
                data['error'] = 'verification code error'
            else:
                sql_select = 'select user_name,password from user where user_name = "' + requset.POST['user_name'] + \
                             '" and password = "'+ requset.POST['password'] + '"'
                result_row = sql_execute(sql_select)
                status = 0
                if len(result_row):
                    data['message'] = 'login successfully'
                else:
                    data['message'] = 'login failure'
        except Exception as e:
            status = 2
            data = {'error': e}
        return JsonResponse({'status': status, 'data': data})
    elif requset.method == 'GET':
        return JsonResponse({'status': 1, 'data': {'error': 'only post allow'}})
    else:
        return JsonResponse({'status': 3, 'data': {'error': 'invalid post'}})


def login2(requset):
    if requset.method == 'POST':
        session_key = requset.POST.get('session_key', 'null')
        __read_session(session_key)
        return JsonResponse({'status': 0, 'data': {'session_key': 'success'}})
    elif requset.method == 'GET':
        return JsonResponse({'status': 1, 'data': {'error': 'only post allow'}})
    else:
        return JsonResponse({'status': 3, 'data': {'error': 'invalid post'}})



