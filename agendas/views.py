# -*- coding: utf-8 -*-

from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.http import HttpResponseRedirect, HttpResponse
from django.template import RequestContext
from models import *
from contrapartes.models import *
from forms import *
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.generic import generic_inlineformset_factory
from django.utils import simplejson
import datetime
from django.template.defaultfilters import escape
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
# Create your views here.

@login_required
def crear_agenda(request):
    if request.method == 'POST':
        form = AgendaForm(request.POST, request.FILES)
        form1 = DocuForm(request.POST, request.FILES)

        if form.is_valid() and form1.is_valid():
            form_uncommited = form.save(commit=False)
            form_uncommited.user = request.user
            form_uncommited.save()
            if form1.cleaned_data['nombre_doc'] != '':
                form1_uncommitd = form1.save(commit=False)
                form1_uncommitd.content_object = form_uncommited
                form1_uncommitd.save()
            return HttpResponseRedirect('/agendas/calendario')
    else:
        form = AgendaForm()
        form1 = DocuForm()
    return render_to_response('agendas/crear_agenda.html', locals(),
    	                         context_instance=RequestContext(request))

@login_required
def editar_agenda(request, id):
    agenda = get_object_or_404(Agendas, id=id)
    #agenda_type = ContentType.objects.get(app_label="foros",model="documentos")
    #docu = agenda_type.get_object_for_this_type(object_id=id)
    AgendaFormSet = generic_inlineformset_factory(Documentos, extra=2)
    form1 = AgendaFormSet(instance=agenda)

    if not agenda.user.userprofile.contraparte == request.user.userprofile.contraparte:
    	return HttpResponse("Usted no puede editar esta Agenda")

    if request.method == 'POST':
        form = AgendaForm(request.POST, instance = agenda)
        form1 = AgendaFormSet(data=request.POST, files=request.FILES, instance = agenda)
    	if form.is_valid() and form1.is_valid():
            form_uncommited = form.save(commit=False)
            form_uncommited.user = request.user
            form_uncommited.save()

            #form1_uncommitd = form1.save(commit=False)
            #form1_uncommitd.content_object = form_uncommited
            #form1_uncommitd.save()
            form1.save()
            return HttpResponseRedirect('/agendas/calendario/?shva=editada')
    else:
        form = AgendaForm(instance=agenda)
        form1 = AgendaFormSet(instance=agenda)
        
    return render_to_response('agendas/crear_agenda.html', locals(),
    	                         context_instance=RequestContext(request))

@login_required
def borrar_agenda(request, id):
    agenda = get_object_or_404(Agendas, pk=id)

    if agenda.user == request.user or request.user.is_superuser:
        agenda.delete()
        return redirect('/agendas/calendario/?shva=erase')
    else:
        return redirect('/')

@login_required
def calendario(request,id=None):
    paises = Pais.objects.all()
    contrapartes = Contraparte.objects.filter(visible=True)

    if request.is_ajax():
        start = datetime.datetime.fromtimestamp(float(request.GET['start']))
        end = datetime.datetime.fromtimestamp(float(request.GET['end']))
        fecha1 = datetime.date(start.year, start.month, start.day)
        fecha2 = datetime.date(end.year, end.month, end.day)
        
        eventos = Agendas.objects.filter(inicio__range=(fecha1, fecha2), user__userprofile__contraparte=request.user.userprofile.contraparte)
        var = []        
        for evento in eventos:
            d = {
                 'id': str(evento.id),
                 'title': u'%s' % (evento.evento), 
                 'start':str(evento.inicio), 
                 'end':str(evento.final), 
                 'allDay': True,
                 'color':str(evento.user.userprofile.contraparte.font_color)
                 }
            var.append(d)
        return HttpResponse(simplejson.dumps(var), mimetype='application/json')
    if not id==None:
        actividad = Agendas.objects.get(pk=id)
    return render_to_response('agendas/agenda_list.html',locals(),
                              context_instance = RequestContext(request))

def calendario_publico(request,id=None):
    paises = Pais.objects.all()
    contrapartes = Contraparte.objects.filter(visible=True)
    if request.is_ajax():
        start = datetime.datetime.fromtimestamp(float(request.GET['start']))
        end = datetime.datetime.fromtimestamp(float(request.GET['end']))
        fecha1 = datetime.date(start.year, start.month, start.day)
        fecha2 = datetime.date(end.year, end.month, end.day)
        
        eventos = Agendas.objects.filter(inicio__range=(fecha1, fecha2),publico=True)
        var = []        
        for evento in eventos:
            d = {
                 'id': str(evento.id),
                 'title': u'%s' % (evento.evento), 
                 'start':str(evento.inicio), 
                 'end':str(evento.final), 
                 'allDay': True,
                 'color':str(evento.user.userprofile.contraparte.font_color),
                 }
            var.append(d)
        return HttpResponse(simplejson.dumps(var), mimetype='application/json')

    if not id==None:
        actividad = Agendas.objects.get(pk=id)
    return render_to_response('agendas/agenda_list_public.html',locals(),
                              context_instance = RequestContext(request))

@login_required
def calendario_full_contraparte(request,id=None):
    paises = Pais.objects.all()
    if request.method == 'POST':
        request.session['p'] = request.POST.getlist('contraparte')
        
    if request.is_ajax():
        start = datetime.datetime.fromtimestamp(float(request.GET['start']))
        end = datetime.datetime.fromtimestamp(float(request.GET['end']))
        fecha1 = datetime.date(start.year, start.month, start.day)
        fecha2 = datetime.date(end.year, end.month, end.day)

        
        eventos = Agendas.objects.filter(inicio__range=(fecha1, fecha2),
                  user__userprofile__contraparte__id__in=request.session['p'])
        
        var = []        
        for evento in eventos:
            d = {
                 'id': str(evento.id),
                 'title': u'%s' % (evento.evento), 
                 'start':str(evento.inicio), 
                 'end':str(evento.final), 
                 'allDay': True,
                 'color':str(evento.user.userprofile.contraparte.font_color)
                 }
            var.append(d)
        return HttpResponse(simplejson.dumps(var), mimetype='application/json')
    if not id==None:
        actividad = Agendas.objects.get(pk=id)
    contrapartes_sel = Contraparte.objects.filter(id__in=request.session['p'])
    contrapartes_otras = Contraparte.objects.exclude(id__in=request.session['p'])
    return render_to_response('agendas/agenda_list_full.html',locals(),
                              context_instance = RequestContext(request))


def documento_publicos(request):
    documentos = Documentos.objects.order_by('-id')
    tags = []
    for docu in Documentos.objects.all():
        for tag in Tag.objects.filter(name=docu.tags_doc):
            tags.append(tag)

    query = request.GET.get('q', '')
    if query:
        result_documento = Documentos.objects.filter(nombre_doc__icontains=query)
        result_tags = Tag.objects.filter(name__icontains=query)
        lista = []
        tags_lista = []
        for n in result_documento:
            lista.append(n)
        for rtag in result_tags:
            TaggedItems = TaggedItem.objects.get_by_model(Documentos, rtag.name)
            if not rtag.items.all().count() == 0:
                li = []
                for it in rtag.items.all():
                    if it.object:
                        li.append(it)
                tags_lista.append({'name':rtag.name, 'count': len(li)})
            for item in TaggedItems:
                lista.append(item)
        #tags.sort(key=operator.itemgetter('count'), reverse=True)
        documentos = list(set(lista))

    paginator = Paginator(documentos, 10)

    page = request.GET.get('page')
    try:
        notas = paginator.page(page)
    except PageNotAnInteger:
        notas = paginator.page(1)
    except EmptyPage:
        notas = paginator.page(paginator.num_pages)

    return render_to_response('agendas/documentos.html', RequestContext(request, locals()))


def busqueda_tag_publico(request, tags):
    tag_sel = get_object_or_404(Tag, name=tags)
    tags = []
    for docu in Documentos.objects.all():
        for tag in Tag.objects.filter(name=docu.tags_doc):
            tags.append(tag)
    todos = TaggedItem.objects.get_by_model(Documentos, tag_sel.name)
    return render_to_response('agendas/documentos_tag.html', RequestContext(request, locals()))

