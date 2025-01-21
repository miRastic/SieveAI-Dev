from ..process.ranking import PluginRankingBase

class CompositeIndexRanker(PluginRankingBase):
  def __init__(self, *args, **kwargs):
    super().__init__(**kwargs)

  def rank_conformers(self, *args, **kwargs):
    """Composite Index Rank Calculation

    :param data|0: PD.DataFrame
    :param ranking_columns_order|1: dict (default {'Score': True})
    :param grouper|2: str (default Ligand)
    :param rank_column|3: str (default Rank)

    :return: (All Ranked Conformers, Top Ranked Conformers)

    """
    _data = kwargs.get('data', args[0] if len(args) > 0 else None)
    _ranking_columns_order = kwargs.get('ranking_columns_order', args[1] if len(args) > 1 else {'Score': True})
    _grouper = kwargs.get('grouper', args[2] if len(args) > 2 else 'Ligand')
    _rank_col_name = kwargs.get('rank_column', args[3] if len(args) > 3 else 'Composite_Rank')

    self.require('pandas', 'PD')

    if not isinstance(_data, self.PD.DataFrame):
      self.log_error('Data is not instance of PD.DataFrame')
      return

    _data = _data.fillna(0)
    _data = _data.reset_index(drop=True)

    _ranking_cols = []
    for _rc, _rval in _ranking_columns_order.items():
      _rc_rank_col = f"{_rc}__RANK"
      _ranking_cols.append(_rc_rank_col)
      _data[_rc] = self.PD.to_numeric(_data[_rc], errors='coerce')
      _data[_rc] = _data[_rc].fillna(_data[_rc].mean())
      _data[_rc_rank_col] = _data[_rc].rank(ascending=_rval)

    _score_col_name = 'Composite_Score'
    _data[_score_col_name] = _data[_ranking_cols].sum(axis='columns')

    _data[list(_ranking_columns_order.keys())] = _data[list(_ranking_columns_order.keys())].round(4)

    _data[_rank_col_name] = _data[_score_col_name].rank(ascending=True, method='dense').astype(int)
    _data = _data.sort_values(_score_col_name, ascending=True)

    _top_res = _data.groupby(_grouper).apply(lambda _row: _row.loc[_row[_rank_col_name].idxmin()])
    _top_res[_rank_col_name] = _top_res[_rank_col_name].rank(ascending=True, method='dense').astype(int)
    _top_res = _top_res.sort_values(_rank_col_name)

    _top_res = _top_res.reset_index(drop=True)

    # Top Results with Ranking
    _top_res = _top_res.sort_values(_rank_col_name)

    return _data, _top_res
