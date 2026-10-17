"""Strict, versioned Practice schema and answer validation."""
import json
import re
from decimal import Decimal

from django.core.exceptions import ValidationError

IDENTIFIER = re.compile(r'^[a-z][a-z0-9_]{0,63}$')
TYPES = {'short_text', 'long_text', 'single_choice', 'multiple_choice', 'integer', 'decimal_amount'}
TEXT_TYPES = {'short_text', 'long_text'}
# Owner-approved Practice limits (PRS-01..PRS-04). Lengths are Unicode code points.
MAX_TEXT = {'short_text': 280, 'long_text': 10_000}
MAX_LABEL = 500
MAX_QUESTIONS = 100
MAX_OPTIONS = 100
MAX_SCHEMA_BYTES = 256 * 1024
MAX_DEPTH = 8
MAX_FRACTION_DIGITS = 2


def _object(value, message):
    if not isinstance(value, dict):
        raise ValidationError(message)
    return value


def _keys(value, required, optional=()):
    if not required.issubset(value) or not set(value).issubset(required | set(optional)):
        raise ValidationError('Practice schema has missing or unsupported fields.')


def _positive_int(value):
    return type(value) is int and value > 0


def _depth(value, level=1):
    if isinstance(value, (dict, list)):
        children = value.values() if isinstance(value, dict) else value
        return max([level] + [_depth(child, level + 1) for child in children])
    return level


def _check_size_and_depth(schema):
    try:
        encoded = json.dumps(schema, separators=(',', ':'), ensure_ascii=False).encode('utf-8')
        too_deep = _depth(schema) > MAX_DEPTH
    except (TypeError, ValueError, RecursionError):
        raise ValidationError('Practice schema is malformed.')
    if len(encoded) > MAX_SCHEMA_BYTES:
        raise ValidationError('Practice schema is too large.')
    if too_deep:
        raise ValidationError('Practice schema is nested too deeply.')


def validate_schema(schema):
    if isinstance(schema, str):
        try:
            schema = json.loads(schema, object_pairs_hook=_unique_pairs)
        except (ValueError, UnicodeError):
            raise ValidationError('Practice schema is malformed.')
    schema = _object(schema, 'Practice schema must be an object.')
    if set(schema) != {'schema_version', 'questions'} or type(schema.get('schema_version')) is not int or schema['schema_version'] != 1:
        raise ValidationError('Practice schema version or fields are unsupported.')
    _check_size_and_depth(schema)
    questions = schema['questions']
    if not isinstance(questions, list):
        raise ValidationError('Practice questions must be a list.')
    if len(questions) > MAX_QUESTIONS:
        raise ValidationError('A Practice activity may have at most 100 questions.')
    seen = set()
    for q in questions:
        q = _object(q, 'Each Practice question must be an object.')
        _keys(q, {'id', 'type', 'label', 'required'}, {'constraints', 'options'})
        qid, kind, label = q['id'], q['type'], q['label']
        if not isinstance(qid, str) or not IDENTIFIER.fullmatch(qid) or qid in seen:
            raise ValidationError('Practice question IDs must be unique valid identifiers.')
        seen.add(qid)
        if not isinstance(kind, str) or kind not in TYPES or not isinstance(label, str) or not label.strip() or type(q['required']) is not bool:
            raise ValidationError('Practice question fields are invalid.')
        if len(label) > MAX_LABEL:
            raise ValidationError('Question labels may be at most 500 characters.')
        constraints = q.get('constraints')
        if kind in TEXT_TYPES:
            if not isinstance(constraints, dict) or set(constraints) != {'max_length'} or not _positive_int(constraints['max_length']) or 'options' in q:
                raise ValidationError('Text question constraints are invalid.')
            if constraints['max_length'] > MAX_TEXT[kind]:
                raise ValidationError(f'{kind} answers may be at most {MAX_TEXT[kind]} characters.')
        elif kind in {'single_choice', 'multiple_choice'}:
            options = q.get('options')
            if 'constraints' in q or not isinstance(options, list) or not options:
                raise ValidationError('Choice question options are invalid.')
            if len(options) > MAX_OPTIONS:
                raise ValidationError('A choice question may have at most 100 options.')
            option_ids = set()
            for option in options:
                option = _object(option, 'Choice options must be objects.')
                if set(option) != {'id', 'label'} or not isinstance(option['id'], str) or not IDENTIFIER.fullmatch(option['id']) or option['id'] in option_ids or not isinstance(option['label'], str) or not option['label'].strip():
                    raise ValidationError('Choice option fields are invalid.')
                if len(option['label']) > MAX_LABEL:
                    raise ValidationError('Option labels may be at most 500 characters.')
                option_ids.add(option['id'])
        elif kind == 'integer':
            if 'options' in q or ('constraints' in q and (not isinstance(constraints, dict) or not set(constraints).issubset({'minimum', 'maximum'}) or any(type(v) is not int for v in constraints.values()) or ('minimum' in constraints and 'maximum' in constraints and constraints['minimum'] > constraints['maximum']))):
                raise ValidationError('Integer constraints are invalid.')
        else:
            if 'options' in q or not isinstance(constraints, dict) or not {'currency'}.issubset(constraints) or not set(constraints).issubset({'currency', 'minimum', 'maximum'}) or constraints['currency'] != 'KES':
                raise ValidationError('Decimal amount constraints are invalid.')
            bounds = [constraints[k] for k in ('minimum', 'maximum') if k in constraints]
            if any(not isinstance(v, str) or not re.fullmatch(r'-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?', v) or v in {'-0', '-0.0', '-0.00'} for v in bounds):
                raise ValidationError('Decimal amount bounds are invalid.')
            if len(bounds) == 2 and Decimal(bounds[0]) > Decimal(bounds[1]):
                raise ValidationError('Decimal amount bounds are invalid.')
    return schema


def _unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate key')
        result[key] = value
    return result


def validate_answer(question, value):
    kind = question['type']
    if value is None:
        raise ValidationError('Null is not a valid Practice answer.')
    if kind in TEXT_TYPES:
        if not isinstance(value, str) or len(value) > question['constraints']['max_length']:
            raise ValidationError('Enter text within the allowed length.')
        return value
    if kind == 'single_choice':
        allowed = {o['id'] for o in question['options']}
        if not isinstance(value, str) or value not in allowed:
            raise ValidationError('Choose one of the listed options.')
        return value
    if kind == 'multiple_choice':
        allowed = {o['id'] for o in question['options']}
        if not isinstance(value, list) or any(not isinstance(v, str) or v not in allowed for v in value) or len(value) != len(set(value)):
            raise ValidationError('Choose valid options without duplicates.')
        return value
    if kind == 'integer':
        if type(value) is not int:
            raise ValidationError('Enter a whole number.')
        limits = question.get('constraints', {})
        if ('minimum' in limits and value < limits['minimum']) or ('maximum' in limits and value > limits['maximum']):
            raise ValidationError('The whole number is outside the allowed range.')
        return value
    if not isinstance(value, str) or not re.fullmatch(r'-?(?:0|[1-9][0-9]*)(?:\.[0-9]{1,%d})?' % MAX_FRACTION_DIGITS, value) or value in {'-0', '-0.0', '-0.00'}:
        raise ValidationError('Enter a KES amount with at most two decimal places.')
    amount = Decimal(value)
    constraints = question['constraints']
    if ('minimum' in constraints and amount < Decimal(constraints['minimum'])) or ('maximum' in constraints and amount > Decimal(constraints['maximum'])):
        raise ValidationError('The amount is outside the allowed range.')
    return value


def validate_response_set(schema, responses, *, complete):
    schema = validate_schema(schema)
    if not isinstance(responses, dict):
        raise ValidationError('Responses must be an object.')
    questions = {q['id']: q for q in schema['questions']}
    if not set(responses).issubset(questions):
        raise ValidationError('Responses contain an unknown question.')
    validated = {}
    for qid, value in responses.items():
        question = questions[qid]
        validated[qid] = validate_answer(question, value)
    if complete:
        for qid, question in questions.items():
            if qid not in validated:
                if question['required']:
                    raise ValidationError({qid: 'This answer is required.'})
                continue
            value = validated[qid]
            if question['required'] and ((isinstance(value, str) and not value.strip()) or (isinstance(value, list) and not value)):
                raise ValidationError({qid: 'This answer is required.'})
    return validated
