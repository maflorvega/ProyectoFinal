(function() {
    var DashboardCtrl = function($scope, Events, Widget, FavoriteDashboards, FileSaver, $routeParams, $location, $http, $timeout, $modal, $q, Dashboard, Parameters) {
      $scope.downloadingPDF = false;
      $scope.downloadingXLS = false;
      //flag to know if dates are completed and enable export
      $scope.datesCompleted = false;

    var searchParams = $location.search();

    $scope.openExportMoMModal = function() {
      var currentParams = $location.search();
      var modalInstance = $modal.open({
        templateUrl: '../../../views/modals/exportMoM.html',
        controller: 'ExportMoMModalCtrl',
        size: 'lg',
        resolve: {
          dateRanges: function () {
            return $scope.dateRanges;
          },
          widgets: function() {
            return getSelectedWidgets();
          },
          searchParams: function() {
            return currentParams;
          }
        }
      });
    };
      /**
      * toggleFavorite Add/Remove the current dashboard to favorite
      */
      $scope.toggleFavorite = function(value) {
        FavoriteDashboards.updateFavorite({dashboardId: $scope.dashboard.id, flag: value});
      };

      //if user has selected dates, then enable MoM export
      if (searchParams.p_startdate && searchParams.p_enddate) {
          $scope.datesCompleted = true;
          var startDateParts = searchParams.p_startdate.split('-');
          var endDateParts = searchParams.p_enddate.split('-');
          var startDate = new Date(startDateParts[0], startDateParts[1] - 1, startDateParts[2]);
          var endDate = new Date(endDateParts[0], endDateParts[1] - 1, endDateParts[2]);
          var dateRanges = [];
          var itStartDate = new Date(startDate.getFullYear(), startDate.getMonth(), startDate.getDate());
          var itEndDate = new Date(itStartDate.getFullYear(), itStartDate.getMonth() + 1, 0);
          while (itEndDate < endDate) {
            dateRanges.push({'start': itStartDate, 'end': itEndDate});
            itStartDate = new Date(itStartDate.getFullYear(), itStartDate.getMonth() + 1, 1);
            // Last day of startDate's month
            // First day of the next months
            itEndDate = new Date(itStartDate.getFullYear(), itStartDate.getMonth() + 1, 0);
          }
          dateRanges.push({'start': itStartDate, 'end': endDate});
          $scope.dateRanges = dateRanges;
      };

      /**
       * changeCollapseValues for each widget sets the value received by param
       * @param  {boolean} value
       */
      $scope.changeCollapseValues = function(value) {
        if ($scope.dashboard.widgets !== undefined) {
          _.forEach($scope.dashboard.widgets, function(widget) {
            _.forEach(widget, function(w) {
              w.isCollapsed = value;
            })
          })
        }
      };

      /**
       * collapseValue Get the collapse value depending if the first widget is visualization
       *
       */
      $scope.collapseValue = function() {
        if ($scope.dashboard.widgets !== undefined) {
          _.forEach($scope.dashboard.widgets, function(widget) {
            _.forEach(widget, function(w) {
              if (w.visualization) {
                w.isCollapsed = false;
              }
            });
          });
        }
      };


      /**
       * exportWidgets For Each selected visualization widget export its svg to a pdf
       */
      $scope.exportWidgetsToPdf = function() {
        var $chart,
          data = {data: []};
        $scope.downloadingPDF = true;
        //generate data to be exported for every widget that is marked for export
        _.forEach($scope.dashboard.widgets, function(widget) {
          _.forEach(widget, function(w) {
            if (isExportable(w)) {
              //to export charts, send SVG
              if (w.visualization && w.visualization.type==='CHART') {
                $chart = $('#' + w.id).find('div[data-highcharts-chart]');
                data.data.push({
                  name: (w.options.exportable.name || w.query.name) + '- ' + w.visualization.name,
                  data: $chart.highcharts().getSVG(),
                  type: 'SVG'
                });
              } else { //to export tables, send data
                data.data.push({
                  name: w.options.exportable.name || w.query.name,
                  data: {
                    columnNames: w.query.queryResult.columnNames,
                    rows: w.query.queryResult.filteredData
                  },
                  type: 'TABLE'
                });
              }
            }
          });
        });

        if (data.data.length) {
          $http({
            url: '/services/pdf/create',
            method: 'POST',
            data: data,
            headers: {
              'Content-Type': 'application/x-www-form-urlencoded'
            },
            responseType: 'arraybuffer'
          }).then(function(response) {
            var blob = new Blob([response.data], {
              type: 'application/pdf;charset=utf-8'
            });
            FileSaver.saveAs(blob, $scope.dashboard.name + '.pdf');
            $scope.downloadingPDF = false;
          }, function() {
            $scope.downloadingPDF = false;
          });
        } else {
          $scope.downloadingPDF = false;
        }
      };

      /**
       * getColumnNames Returns columns to export for a given widget. If it is a custom
       * table then there may be hidden columns
       * @return {array}
      */
      var getColumnNames = function(widget) {
        var columnsUsed = widget.query.queryResult.getColumnCleanNames();
        if (widget.visualization && widget.visualization.type === 'CUSTOM TABLE' && widget.visualization.options.cols) {
          var visibleColumns = {};
          columnsUsed = [];
          _.forEach(widget.visualization.options.cols, function(option) {
            visibleColumns[option.column] = option.visible;
          });
          _.forEach(widget.query.queryResult.getColumnCleanNames(), function(col, i) {
            if (visibleColumns[col] === undefined || visibleColumns[col] !== false) {
              columnsUsed.push(col);
            }
          });
        }
        return columnsUsed;
      };

      /**
       * excelFilters Creates a object that contains all the filters included on the dashboard
       * excluding some parameters like maxAge
       * @return {array}
       */
      var excelFilters = function() {
        var params = $location.search();
        var blacklist = Parameters.getBlackListParameters();
        var parameters = {};
        for (var propertyName in params) {
          if (!_.contains(blacklist, propertyName)) {
            var filterName = (propertyName.slice(0, 2) === 'p_' ? propertyName.slice(2) : propertyName);
            parameters[filterName] = params[propertyName];
          }
        }
        if (parameters.length !== 0) {
          return parameters;
        }
        return null;
      };

      /*
      * Give a widget, return true if it is exportable and marked to export
      */
      var isExportable = function(w) {
        return w.options.exportable !== undefined &&
          w.options.exportable.isExportable &&
          w.query !== undefined &&
          w.query.queryResult !== undefined &&
          w.query.queryResult.filteredData !== undefined;
      };

      /*
      * Returns all widget ids that are exportable and marked to export
      */
      var getSelectedWidgets = function() {
        var results = [];
        _.forEach($scope.dashboard.widgets, function(widget) {
          _.forEach(widget, function(w) {
            if (isExportable(w)) {
              results.push({id: w.id, columnNames: w.query.queryResult.columnNames});
            }
          });
        });
        return results; //_.pluck(results, 'id');
      };

      /**
       * exportWidgets For Each widget takes the data and exports that on a Sheet (xls)
       */
      $scope.exportWidgets = function() {
        $scope.downloadingXLS = true;
        var report = {
          name: $scope.dashboard.name,
          filters: excelFilters(),
          sheets: [],
        };

        //generate data to be exported for every widget that is marked for export
        _.forEach($scope.dashboard.widgets, function(widget) {
          _.forEach(widget, function(w) {
            if (isExportable(w)) {
              // Creates a new option for adding the sheet name
              if (w.options.exportable.name === undefined) {
                w.options.exportable.name = w.query.name;
              }
              worksheet = {
                meta: {
                  name: w.options.exportable.name, //title
                  description: w.query.description, //subtitle
                  columnNames: getColumnNames(w),
                  autofilter: true
                },
                rows: w.query.queryResult.filteredData
              };
              report.sheets.push(worksheet);
            }
          });
        });
        if (report.sheets.length > 0) {
          $http({
            url: '/api/dashboard/generate_excel',
            method: 'POST',
            data: report,
            headers: {
              'Content-type': 'application/json'
            },
            responseType: 'arraybuffer'
          }).then(function(response) {
            var blob = new Blob([response.data], {
              type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;charset=utf-8"
            });

            FileSaver.saveAs(blob, $scope.dashboard.name + '.xlsx');
            $scope.downloadingXLS = false;
          }, function() {
            $scope.downloadingXLS = false;
          });
        } else {
          $scope.downloadingXLS = false;
        }
      }

  $scope.refreshEnabled = false; $scope.refreshRate = 60;

  var loadDashboard = _.throttle(function() {
    $scope.dashboard = Dashboard.get({
      slug: $routeParams.dashboardSlug
    }, function(dashboard) {
      Events.record(currentUser, "view", "dashboard", dashboard.id);

      FavoriteDashboards.getFavoriteStatus({dashboardId: $scope.dashboard.id}, function(result) {
        $scope.isFavorite = result.flag;
      });

      $scope.$parent.pageTitle = dashboard.name;

      var promises = [];

      $scope.dashboard.widgets = _.map($scope.dashboard.widgets, function(row) {
        return _.map(row, function(widget) {
          var w = new Widget(widget);

          if (w.visualization) {
            promises.push(w.getQuery().getQueryResult().toPromise());
          }

          return w;
        });
      });

      $q.all(promises).then(function(queryResults) {
        var filters = {};
        _.each(queryResults, function(queryResult) {
          var queryFilters = queryResult.getFilters();
          _.each(queryFilters, function(queryFilter) {
            var hasQueryStringValue = _.has($location.search(), queryFilter.name);

            if (!(hasQueryStringValue || dashboard.dashboard_filters_enabled)) {
              // If dashboard filters not enabled, or no query string value given, skip filters linking.
              return;
            }

            if (!_.has(filters, queryFilter.name)) {
              var filter = _.extend({}, queryFilter);
              filters[filter.name] = filter;
              filters[filter.name].originFilters = [];
              if (hasQueryStringValue) {
                filter.current = $location.search()[filter.name];
              }

              $scope.$watch(function() {
                return filter.current
              }, function(value) {
                _.each(filter.originFilters, function(originFilter) {
                  originFilter.current = value;
                });
              });
            }

            // TODO: merge values.
            filters[queryFilter.name].originFilters.push(queryFilter);
          });
        });

        $scope.filters = _.values(filters);
      });


    }, function() {
      // error...
      // try again. we wrap loadDashboard with throttle so it doesn't happen too often.\
      // we might want to consider exponential backoff and also move this as a general solution in $http/$resource for
      // all AJAX calls.
      loadDashboard();
    });
  }, 1000);

  loadDashboard();

  var autoRefresh = function() {
    if ($scope.refreshEnabled) {
      $timeout(function() {
        Dashboard.get({
          slug: $routeParams.dashboardSlug
        }, function(dashboard) {
          var newWidgets = _.groupBy(_.flatten(dashboard.widgets), 'id');

          _.each($scope.dashboard.widgets, function(row) {
            _.each(row, function(widget, i) {
              var newWidget = newWidgets[widget.id];
              if (newWidget && newWidget[0].visualization.query.latest_query_data_id != widget.visualization.query.latest_query_data_id) {
                row[i] = new Widget(newWidget[0]);
              }
            });
          });

          autoRefresh();
        });

      }, $scope.refreshRate);
    }
  };

  $scope.archiveDashboard = function() {
    if (confirm('Are you sure you want to archive the "' + $scope.dashboard.name + '" dashboard?')) {
      Events.record(currentUser, "archive", "dashboard", $scope.dashboard.id);
      $scope.dashboard.$delete(function() {
        $scope.$parent.reloadDashboards();
      });
    }
  }

  $scope.triggerRefresh = function() {
    $scope.refreshEnabled = !$scope.refreshEnabled;

    Events.record(currentUser, "autorefresh", "dashboard", dashboard.id, {
      'enable': $scope.refreshEnabled
    });

    if ($scope.refreshEnabled) {
      var refreshRate = _.min(_.map(_.flatten($scope.dashboard.widgets), function(widget) {
        var schedule = widget.visualization.query.schedule;
        if (schedule === null || schedule.match(/\d\d:\d\d/) !== null) {
          return 60;
        }
        return widget.visualization.query.schedule;
      }));

      $scope.refreshRate = _.max([120, refreshRate * 2]) * 1000;

      autoRefresh();
    }
  };
};

var WidgetCtrl = function($scope, $location, Events, Query, Parameters) {

  Parameters.setParameters($location.search());

  $scope.deleteWidget = function() {
    if (!confirm('Are you sure you want to remove "' + $scope.widget.getName() + '" from the dashboard?')) {
      return;
    }

    Events.record(currentUser, "delete", "widget", $scope.widget.id);

    $scope.widget.$delete(function() {
      $scope.dashboard.widgets = _.map($scope.dashboard.widgets, function(row) {
        return _.filter(row, function(widget) {
          return widget.id != undefined;
        })
      });
    });
  };

  Events.record(currentUser, "view", "widget", $scope.widget.id);

  if ($scope.widget.visualization) {
    Events.record(currentUser, "view", "query", $scope.widget.visualization.query.id);
    Events.record(currentUser, "view", "visualization", $scope.widget.visualization.id);

    $scope.query = $scope.widget.getQuery();
    var parameters = Query.collectParamsFromQueryString($location, $scope.query);
    var maxAge = $location.search()['maxAge'];
    $scope.queryResult = $scope.query.getQueryResult(maxAge, parameters);
    $scope.type = 'visualization';

    $scope.missingParameters = false;
    var requiredParameters = $scope.query.getParameters();
    // Searchs if all the parameters are instantiated
    for (var i = 0; i < requiredParameters.length; i++) {
      if (parameters[requiredParameters[i]] === undefined) {
        $scope.missingParameters = true;
      }
    }
  } else {
    $scope.type = 'textbox';
  }

  // Listen for url changed
  $scope.$on('$routeUpdate', function() {
    if ($scope.widget.visualization) {
      // Set missingParameters to false
      $scope.missingParameters = false;
      // Gets query
      $scope.query = $scope.widget.getQuery();
      // Gets the parameters from the query and location
      var parameters = Query.collectParamsFromQueryString($location, $scope.query);
      var maxAge = $location.search()['maxAge'];
      // Calls to query
      $scope.queryResult = $scope.query.getQueryResult(maxAge, parameters);
      var requiredParameters = $scope.query.getParameters();
      // Searchs if all the parameters are instantiated
      for (var i = 0; i < requiredParameters.length; i++) {
        if (parameters[requiredParameters[i]] === undefined) {
          $scope.missingParameters = true;
          return;
        }
      }
    }
  });
};

var ExportMoMModalCtrl = function($scope, $modalInstance, $http, $q, dateRanges, widgets, searchParams) {
  $scope.dateRanges = dateRanges;
  $scope.email = '';

  function getExportData() {
    return {
      selectedMonths: $scope.getSelectedMonths(),
      email: $scope.email,
      widgets: widgets,
      searchParams: searchParams
    };
  };

  /* Set error flag to false to alert does not show up */
  $scope.closeAlert = function() {
    $scope.error = false;
  };

  $scope.getSelectedMonths = function() {
    return _.filter($scope.dateRanges, {isSelected: true});
  };

  $scope.exportMoMXls = function() {
    $http({
      url: '/api/reports/excel_by_month',
      method: 'POST',
      data: getExportData()
    }).then(function() {
      console.log('report request sent');
      $scope.close();
    }, function() {
      $scope.error = true;
    });
  };

  $scope.exportMoMPdf = function() {
    $http({
      url: '',
      method: 'POST',
      data: getExportData()
    }).then(function() {
      console.log('report request sent');
      $scope.close();
    }, function() {
      $scope.error = true;
    });
  };

  $scope.exportMoMBoth = function() {
    var promises = [];
    promises.push($http({
      url: '',
      method: 'POST',
      data: getExportData()
    }));
    promises.push($http({
      url: '',
      method: 'POST',
      data: getExportData()
    }));
    $q.all(promises).then(function() {
      console.log('report request sent');
      $scope.close();
    }, function() {
      $scope.error = true;
    });
  };

  $scope.close = function() {
    $modalInstance.dismiss('cancel');
  };
};

angular.module('redash.controllers')
  .controller('DashboardCtrl', [
    '$scope', 'Events', 'Widget', 'FavoriteDashboards', 'FileSaver', '$routeParams', '$location',
    '$http', '$timeout', '$modal', '$q', 'Dashboard', 'Parameters', DashboardCtrl
  ])
  .controller('WidgetCtrl', [
    '$scope', '$location', 'Events', 'Query', 'Parameters', WidgetCtrl
  ])
  .controller('ExportMoMModalCtrl',
    ['$scope', '$modalInstance', '$http', '$q', 'dateRanges', 'widgets', 'searchParams', ExportMoMModalCtrl
  ])
})();
