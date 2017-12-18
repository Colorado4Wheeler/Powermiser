Powermiser Wish List
==========

Potential future improvements for the plugin, some from users and some thunk up all on my own :)

* Add a warning option to blink or dim the lights when time is about to run out so the person knows it's happening
* Add a maximum time on so the device cannot stay on for more than this amount of time
* Allow "and"/"or" grouping for conditions (this will actually be added to the main core engine in the near future so we only need to add the additional fields in the plugin)
* Clear condition devices when conditions no longer apply, otherwise they continue to be watched and get hidden (this happend with Vera when I disabled the plugin)
* Add integration for excluding HBB devices from the list
* Error: Exception in plugin.processCommand line 154: unexpected EOF while parsing (<unknown>, line 0) CODE: autoOffTimes = ast.literal_eval (parent.states["autoOffTimes"])