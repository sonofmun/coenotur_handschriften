from flask import redirect, request, url_for, g, flash, current_app, render_template
from flask_babel import _
from .Search import advanced_query_index, suggest_word_search
from .forms import AdvancedSearchForm
from app.search import bp
from json import dumps


HIGHLIGHT_MAPPING = {'identifier': _('Signatur'),
                     'ms_item': _('Inhalt'),
                     'provenance': _('Geschichte der Handschrift'),
                     'person.name': _('Name'),
                     'orig_place.place': _('Ort'),
                     'person.role': _('Role'),
                     'person.identifier': _('ID'),
                     'orig_place.cert': _('Sicherheit'),
                     'person': _('Person'),
                     'orig_place': _('Entstehungsort')
                     }


@bp.route("/simple", methods=["GET"])
def r_simple_search() -> redirect:
    if not g.search_form.validate():
        for k, m in g.search_form.errors.items():
            if k == 'simple_q':
                flash(m[0] + _(' Die einfache Suche funktioniert nur mit einem Suchwort.'))
        return redirect(url_for('.r_results', source='simple', simple_q=g.search_form.data['simple_q']))
    data = g.search_form.data
    return redirect(url_for('.r_results', source='simple', sort="urn", **data))


@bp.route("/results", methods=["GET"])
def r_results():
    source = request.args.get('source', None)
    # This means that someone simply navigated to the /results page without any search parameters
    if not source:
        return redirect(url_for('InstanceNemo.r_index'))
    posts_per_page = 10000
    page = 1
    search_args = dict(simple_q=request.args.get('simple_q'),
                       identifier=request.args.get('identifier'),
                       orig_place=request.args.get('orig_place'),
                       orig_place_cert=request.args.get('orig_place_cert'),
                       orig_year_start=request.args.get('orig_year_start'),
                       orig_year_end=request.args.get('orig_year_end'),
                       ms_item=request.args.get('ms_item'),
                       person=request.args.get('person'),
                       person_role=request.args.get('person_role'),
                       person_identifier=request.args.get('person_identifier'),
                       provenance=request.args.get('provenance'),
                       autocomplete_ms_item=request.args.get('autocomplete_ms_item'),
                       autocomplete_person=request.args.get('autocomplete_person'),
                       autocomplete_orig_place=request.args.get('autocomplete_orig_place'),
                       autocomplete_orig_place_cert=request.args.get('autocomplete_orig_place_cert'),
                       autocomplete_person_role=request.args.get('autocomplete_person_role'),
                       autocomplete_person_identifier=request.args.get('autocomplete_person_identifier'),
                       with_digitalisat=request.args.get('with_digitalisat'))
    posts, total, aggs = advanced_query_index(**search_args)
    return render_template('search/search.html', title=_('Suche'), posts=posts, current_page=page,
                           total_results=total, aggs=aggs, highlight_mapping=HIGHLIGHT_MAPPING)


@bp.route("/advanced_search", methods=["GET"])
def r_advanced_search():
    form = AdvancedSearchForm()
    data_present = [x for x in form.data if form.data[x]]
    if form.validate() and data_present and 'submit' in data_present:
        data = form.data
        return redirect(url_for('.r_results', source="advanced", **data))
    for k, m in form.errors.items():
        flash(k + ': ' + m[0])
    return render_template('search/advanced_search.html', form=form)


@bp.route("/doc", methods=["GET"])
def r_search_docs():
    """ Route to the documentation page for the advanced search"""
    return current_app.config['nemo_app'].render(template="search::documentation.html", url=dict())


@bp.route("/suggest/<word>", methods=["GET"])
def word_search_suggester(word: str):
    qSource = request.args.get('qSource', 'text')
    words = suggest_word_search(q=word.lower() if qSource == 'text' else request.args.get('q', '').lower(),
                                lemma_search=request.args.get('lemma_search', 'autocomplete'),
                                fuzziness=request.args.get("fuzziness", "0"),
                                in_order=request.args.get('in_order', 'False'),
                                slop=request.args.get('slop', '0'),
                                year=request.args.get('year', 0, type=int),
                                month=request.args.get('month', 0, type=int),
                                day=request.args.get('day', 0, type=int),
                                year_start=request.args.get('year_start', 0, type=int),
                                month_start=request.args.get('month_start', 0, type=int),
                                day_start=request.args.get('day_start', 0, type=int),
                                year_end=request.args.get('year_end', 0, type=int),
                                month_end=request.args.get('month_end', 0, type=int),
                                day_end=request.args.get('day_end', 0, type=int),
                                date_plus_minus=request.args.get("date_plus_minus", 0, type=int),
                                corpus=request.args.get('corpus', '').split() or ['all'],
                                exclusive_date_range=request.args.get('exclusive_date_range', "False"),
                                composition_place=request.args.get('composition_place', ''),
                                special_days=request.args.get('special_days', '').split(),
                                regest_q=word.lower() if qSource == 'regest' else request.args.get('regest_q', '').lower(),
                                regest_field=request.args.get('regest_field', 'regest'),
                                qSource=request.args.get('qSource', 'text'))
    return dumps(words)